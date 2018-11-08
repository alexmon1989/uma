from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import F
from .models import ObjType, InidCodeSchedule


def simple(request):
    """Отображает страницу с простым одностроковым поиском."""
    return render(request, 'search/simple/simple.html')


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

        # Тестовый поиск по Elastic

        from elasticsearch import Elasticsearch
        from elasticsearch_dsl import Search, Q

        i_11 = 111160
        i_51 = "A61B5/103"
        i_31 = "2010-140155 OR qw"
        i_32 = "2010-06-21"
        i_33 = "JP OR UA"

        client = Elasticsearch()

        qs = Q('query_string', query='ipcCodes.I_11:{}'.format(i_11))
        qs |= Q('nested', path='ipcCodes.IPC', query=Q('query_string', query='ipcCodes.IPC.I_51:"{}"'.format(i_51)))
        qs |= Q('nested', path='ipcCodes.I_30', query=Q('query_string', query='ipcCodes.I_30.I_31:{}'.format(i_31)))
        qs |= Q('nested', path='ipcCodes.I_30', query=Q('query_string', query='ipcCodes.I_30.I_32:{}'.format(i_32)))
        qs |= Q('nested', path='ipcCodes.I_30', query=Q('query_string', query='ipcCodes.I_30.I_33:{}'.format(i_33)))

        s = Search(using=client, index="uma").query(qs)

        response = s.execute()
        context['elastic_results'] = response

        return context
