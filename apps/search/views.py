from django.views.generic import TemplateView
from django.db.models import F
from django.forms import formset_factory, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.utils.http import urlencode
from django.shortcuts import redirect, reverse
from django.views.decorators.http import require_POST
from .models import ObjType, InidCodeSchedule, SimpleSearchField, AppDocuments
from .forms import AdvancedSearchForm, SimpleSearchForm
from .utils import get_search_groups, elastic_search_groups, count_obj_types_filtered, count_obj_states_filtered
from operator import attrgetter
from urllib.parse import parse_qs
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


class SimpleListView(TemplateView):
    """Отображает страницу с возможностью простого поиска."""
    template_name = 'search/simple/simple.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        lang_code = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Параметры поиска
        context['search_parameter_types'] = list(SimpleSearchField.objects.annotate(
            field_label=F(f"field_label_{lang_code}")
        ).values(
            'id',
            'field_label',
            'field_name'
        ).filter(is_visible=True))

        context['initial_data'] = {'form-TOTAL_FORMS': 1}
        SimpleSearchFormSet = formset_factory(SimpleSearchForm)
        if self.request.GET:
            formset = SimpleSearchFormSet(self.request.GET)
            context['initial_data'] = dict(formset.data.lists())

        return context


class AdvancedListView(TemplateView):
    """Отображает страницу с возможностью расширенного поиска."""
    template_name = 'search/advanced/advanced.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Типы ОПС
        context['obj_types'] = list(
            ObjType.objects.order_by('id').annotate(value=F(f"obj_type_{context['lang_code']}")).values('id', 'value')
        )

        # ИНИД-коды вместе с их реестрами
        context['ipc_codes'] = InidCodeSchedule.get_ipc_codes_with_schedules(context['lang_code'])

        context['initial_data'] = {'form-TOTAL_FORMS': 1}
        AdvancedSearchFormSet = formset_factory(AdvancedSearchForm)
        if self.request.GET:
            formset = AdvancedSearchFormSet(self.request.GET)

            # Иниц. данные для формы
            context['initial_data'] = dict(formset.data.lists())

            # Валидация поисковой формы
            try:
                is_valid = formset.is_valid()
            except ValidationError:
                raise Http404("Некоректний пошуковий запит.")

            # Признак того что производится поиск
            context['is_search'] = True

            # Поиск в ElasticSearch
            if is_valid:
                # Разбивка поисковых данных на поисковые группы
                search_groups = get_search_groups(formset.cleaned_data)

                # Поиск по каждой группе
                all_hits = elastic_search_groups(search_groups)

                # Сортировка результатов поиска (обратная сортировка по релевантности)
                all_hits = sorted(all_hits, key=attrgetter('meta.score'), reverse=True)

                # Типы объектов в найденных результатах
                obj_types = [{'id': x['obj_type'].id,
                              'title': getattr(x['obj_type'], f"obj_type_{context['lang_code']}")}
                             for x in search_groups]
                res_obj_types = list({v['id']: v for v in obj_types}.values())

                # Статусы в найденных результатах
                res_obj_states = []
                for i in range(1, 3):
                    count = len(list(filter(lambda x: x['search_data']['obj_state'] == i, all_hits)))
                    if count:
                        res_obj_states.append({'obj_state': i})

                # Фильтрация согласно фильтрам в сайдбаре
                context['results'] = all_hits
                if self.request.GET.get('filter_obj_type'):
                    context['results'] = list(
                        filter(lambda x: str(x['Document']['idObjType']) in self.request.GET.getlist('filter_obj_type'),
                               context['results']))
                if self.request.GET.get('filter_obj_state'):
                    context['results'] = list(
                        filter(lambda x: str(x['search_data']['obj_state']) in self.request.GET.getlist('filter_obj_state'),
                               context['results']))

                # Количество объектов определённых типов в отфильтрованных результатах
                context['res_obj_types'] = count_obj_types_filtered(
                    all_hits,
                    res_obj_types,
                    self.request.GET.getlist('filter_obj_state')
                )

                # Количество объектов определённых статусов в отфильтрованных результатах
                context['res_obj_states'] = count_obj_states_filtered(
                    all_hits,
                    res_obj_states,
                    self.request.GET.getlist('filter_obj_type')
                )

                # Пагинатор
                paginator = Paginator(context['results'], 10)
                context['results'] = paginator.get_page(self.request.GET.get('page'))

        return context


@require_POST
def add_filter_params(request):
    """Формирует строку параметров фильтра и делает переадресацию обратно на страницу поиска."""
    get_params = parse_qs(request.POST.get('get_params'))
    get_params['filter_obj_type'] = request.POST.getlist('filter_obj_type')
    get_params['filter_obj_state'] = request.POST.getlist('filter_obj_state')

    if not get_params['filter_obj_type']:
        del get_params['filter_obj_type']

    if not get_params['filter_obj_state']:
        del get_params['filter_obj_state']

    if get_params.get('page'):
        del get_params['page']  # Для переадресации на 1 страницу

    get_params = urlencode(get_params, True)
    return redirect(f"{reverse('search:advanced')}?{get_params}")


class ObjectDetailView(TemplateView):
    """Отображает страницу с детальной информацией по объекту"""
    hit = None

    def get_template_names(self):
        if self.hit['Document']['idObjType'] in (1, 2):
            return ['search/detail/inv_um/detail.html']

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Поиск в ElasticSearch по номеру заявки, который является _id документа
        id_app_number = kwargs['id_app_number']
        client = Elasticsearch()
        s = Search().using(client).query("match", _id=id_app_number).execute()
        if not s:
            raise Http404("Об'єкт не знайдено")
        context['hit'], self.hit = s[0], s[0]
        context['biblio_data'] = self.hit.Claim if self.hit.search_data.obj_state == 1 else self.hit.Patent

        # Документы заявки (библиографические)
        context['biblio_documents'] = AppDocuments.get_app_documents(id_app_number)

        return context
