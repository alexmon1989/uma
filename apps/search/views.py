from django.views.generic import TemplateView
from django.db.models import F
from django.forms import formset_factory, ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from .models import ObjType, InidCodeSchedule, SimpleSearchField, IpcCode, ElasticIndexField
from .forms import AdvancedSearchForm, SimpleSearchForm
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
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
            ObjType.objects.order_by('id').annotate(value=F(f"obj_type_{context['lang_code']}")).values('id', 'value'))

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

                # Признак того что производится поиск
                context['is_search'] = True
            except ValidationError:
                raise Http404("Некоректний пошуковий запит.")

            # Поиск в ElasticSearch
            if is_valid:
                # Разбивка поисковых данных на поисковые группы
                search_groups = []
                for obj_type in ObjType.objects.all():
                    # Поисковые запросы на заявки
                    search_groups.append({
                        'obj_type': obj_type,
                        'obj_state': 1,
                        'search_params': list(filter(
                            lambda x: x['obj_type'] == obj_type.pk and '1' in x['obj_state'],
                            formset.cleaned_data
                        ))
                    })
                    # Поисковые запросы на охранные документы
                    search_groups.append({
                        'obj_type': obj_type,
                        'obj_state': 2,
                        'search_params': list(filter(
                            lambda x: x['obj_type'] == obj_type.pk and '2' in x['obj_state'],
                            formset.cleaned_data
                        ))
                    })

                # Поиск по каждой группе
                client = Elasticsearch()
                all_hits = []
                for group in search_groups:
                    if group['search_params']:
                        qs = Q('query_string', query=f"{group['obj_type'].pk}", default_field='Document.idObjType')
                        qs &= Q('query_string', query=f"{group['obj_state']}", default_field='Document.Status')

                        for search_param in group['search_params']:
                            # Поле поиска ElasticSearch
                            inid_schedule = InidCodeSchedule.objects.filter(
                                ipc_code__id=search_param['ipc_code'],
                                schedule_type__obj_type=group['obj_type']
                            ).first()

                            # Проверка доступно ли поле для поиска
                            if inid_schedule.enable_search and inid_schedule.elastic_index_field is not None:
                                qs &= Q(
                                    'query_string',
                                    query=f"{search_param['value']}",
                                    default_field=inid_schedule.elastic_index_field.field_name
                                )

                        s = Search(using=client, index="uma").query(qs)
                        group['response'] = s.execute()
                        # Объединение результатов поиска
                        for hit in group['response']:
                            all_hits.append(hit)

                # Сортировка результатов поиска (обратная сортировка по релевантности)
                all_hits = sorted(all_hits, key=attrgetter('meta.score'), reverse=True)

                # Типы объектов в найденных результатах
                context['res_obj_types'] = []
                for obj_type in ObjType.objects.annotate(
                        title=F(f"obj_type_{context['lang_code']}")
                ).values('id', 'title'):
                    count = len(list(filter(
                        lambda x: x['Document']['idObjType'] == obj_type['id'],
                        all_hits
                    )))
                    if count:
                        context['res_obj_types'].append({'obj_type': obj_type})

                # Статусы в найденных результатах
                context['res_obj_states'] = []
                for i in range(1, 3):
                    count = len(list(filter(
                        lambda x: x['Document']['Status'] == i,
                        all_hits
                    )))
                    if count:
                        context['res_obj_states'].append({'obj_state': i})

                # TODO: Фильтрация согласно фильтрам в сайдбаре

                # Пагинатор
                paginator = Paginator(all_hits, 10)
                page = self.request.GET.get('page')
                context['results'] = paginator.get_page(page)

                # Количество объектов определённых типов в отфильтрованных результатах
                for obj_type in context['res_obj_types']:
                    obj_type['count'] = len(list(filter(
                        lambda x: x['Document']['idObjType'] == obj_type['obj_type']['id'],
                        all_hits
                    )))

                # Количество объектов определённых статусов в отфильтрованных результатах
                for obj_state in context['res_obj_states']:
                    obj_state['count'] = len(list(filter(
                        lambda x: x['Document']['Status'] == obj_state['obj_state'],
                        all_hits
                    )))

        return context
