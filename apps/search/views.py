from django.views.generic import TemplateView
from django.db.models import F
from django.forms import formset_factory
from .models import ObjType, InidCodeSchedule, SimpleSearchField, IpcCode, ElasticIndexField
from .forms import AdvancedSearchForm, SimpleSearchForm
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
            print(formset.errors)
            context['initial_data'] = dict(formset.data.lists())

        return context


class AdvancedListView(TemplateView):
    """Отображает страницу с возможностью расширенного поиска."""
    template_name = 'search/advanced/advanced.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        lang_code = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Типы ОПС
        context['obj_types'] = list(
            ObjType.objects.order_by('id').annotate(value=F(f"obj_type_{lang_code}")).values('id', 'value'))

        # ИНИД-коды вместе с их реестрами
        context['ipc_codes'] = InidCodeSchedule.get_ipc_codes_with_schedules(lang_code)

        context['initial_data'] = {'form-TOTAL_FORMS': 1}
        AdvancedSearchFormSet = formset_factory(AdvancedSearchForm)
        if self.request.GET:
            formset = AdvancedSearchFormSet(self.request.GET)
            print(formset.errors)
            context['initial_data'] = dict(formset.data.lists())

            # Поиск в ElasticSearch
            client = Elasticsearch()
            qs = None
            for elastic_field in ElasticIndexField.objects.filter(parent__isnull=True):
                # Список связанных ИНИД-кодов
                ipc_codes = elastic_field.inidcodeschedule_set.all()

                # Проверка есть ли в данных поисковой форме запрос на поиск по этому ИНИД-коду
                # for ipc_code in ipc_codes:
                #     print(ipc_code.ipc_code)


            # Тестовый поиск по Elastic
            I_11 = 78139
            IPC = "C21B13/00"
            I_54 = "РЕГУЛИРОВАНИЕ"
            I_72_N_U = "Метіус Гарі Е."
            I_72_C_U = "US OR UA"
            I_71_N = "МІД?ЕКС* OR aqdasd"
            I_71_C = "CH"

            qs = Q('query_string', query='Patent.I_11:{}'.format(I_11))
            qs &= Q('query_string', query='Patent.IPC:"{}"'.format(IPC))
            qs &= Q('query_string', query='Patent.I_54//*:{}'.format(I_54))

            qs &= Q(
                'nested',
                path='Patent.I_72',
                query=Q('query_string', query='Patent.I_72.I_72.N.U:"{}"'.format(I_72_N_U)) & Q('query_string', query='Patent.I_72.I_72.C.U:{}'.format(I_72_C_U))
            )

            # qs &= Q(
            #     'nested',
            #     path='Patent.I_71',
            #     query=Q('query_string', query='Patent.I_71.I_71.N//*:({})'.format(I_71_N))
            # )

            qs &= Q(
                'nested',
                path='Patent.I_71',
                query=Q('query_string', default_field='Patent.I_71.I_71.N*', analyze_wildcard=True, query=I_71_N)
                      & Q('query_string', default_field='Patent.I_71.I_71.C*', analyze_wildcard=True, query=I_71_C)
            )

            # print(qs)

            s = Search(using=client, index="uma").query(qs)

            response = s.execute()
            context['elastic_results'] = response
            # print(context['elastic_results'])

        return context
