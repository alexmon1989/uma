from django.views.generic import TemplateView
from django.db.models import F
from django.forms import formset_factory, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from .models import ObjType, InidCodeSchedule, SimpleSearchField
from .forms import AdvancedSearchForm, SimpleSearchForm
from .utils import get_search_groups, elastic_search_groups
from operator import attrgetter


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
                context['res_obj_types'] = list({v['id']: v for v in obj_types}.values())

                # Статусы в найденных результатах
                context['res_obj_states'] = []
                for i in range(1, 3):
                    count = len(list(filter(lambda x: x['Document']['Status'] == i, all_hits)))
                    if count:
                        context['res_obj_states'].append({'obj_state': i})

                # TODO: Фильтрация согласно фильтрам в сайдбаре

                # Пагинатор
                paginator = Paginator(all_hits, 10)
                context['results'] = paginator.get_page(self.request.GET.get('page'))

                # Количество объектов определённых типов в отфильтрованных результатах
                for obj_type in context['res_obj_types']:
                    obj_type['count'] = len(list(filter(
                        lambda x: x['Document']['idObjType'] == obj_type['id'],
                        all_hits
                    )))

                # Количество объектов определённых статусов в отфильтрованных результатах
                for obj_state in context['res_obj_states']:
                    obj_state['count'] = len(list(filter(
                        lambda x: x['Document']['Status'] == obj_state['obj_state'],
                        all_hits
                    )))

        return context
