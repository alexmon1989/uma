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
        # Типы ОПС
        context['obj_types'] = list(
            ObjType.objects.order_by('id').annotate(value=F('obj_type_ua')).values('id', 'value'))
        # ИНИД-коды
        ipc_codes = InidCodeSchedule.objects.exclude(ipc_code__isnull=True).filter(enable_view=True).values(
            'ipc_code__id',
            'ipc_code__code_value_ua',
            'ipc_code__obj_type__id',
            'schedule_type__id',
            'ipc_code__code_data_type',
            'ipc_code__obj_type__obj_type_ua'
        )
        ipc_codes_result = {}
        for ipc_code in ipc_codes:
            if not ipc_codes_result.get(ipc_code['ipc_code__id']):
                ipc_codes_result[ipc_code['ipc_code__id']] = {
                    'id': ipc_code['ipc_code__id'],
                    'value': ipc_code['ipc_code__code_value_ua'],
                    'obj_type_id': ipc_code['ipc_code__obj_type__id'],
                    'obj_type': ipc_code['ipc_code__obj_type__obj_type_ua'],
                    'schedule_types': [ipc_code['schedule_type__id']],
                    'data_type': ipc_code['ipc_code__code_data_type'],
                }
            else:
                ipc_codes_result[ipc_code['ipc_code__id']]['schedule_types'].append(ipc_code['schedule_type__id'])
        context['ipc_codes'] = list(ipc_codes_result.values())

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
