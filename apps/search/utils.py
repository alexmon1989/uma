from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from .models import ObjType, InidCodeSchedule


def get_search_groups(search_data):
    """Разбивка поисковых данных на поисковые группы"""
    search_groups = []
    for obj_type in ObjType.objects.all():
        # Поисковые запросы на заявки
        search_groups.append({
            'obj_type': obj_type,
            'obj_state': 1,
            'search_params': list(filter(
                lambda x: x['obj_type'] == obj_type.pk and '1' in x['obj_state'],
                search_data
            ))
        })
        # Поисковые запросы на охранные документы
        search_groups.append({
            'obj_type': obj_type,
            'obj_state': 2,
            'search_params': list(filter(
                lambda x: x['obj_type'] == obj_type.pk and '2' in x['obj_state'],
                search_data
            ))
        })
    # Фильтрация пустых групп
    search_groups = filter(lambda x: len(x['search_params']) > 0, search_groups)
    return list(search_groups)


def elastic_search_groups(search_groups):
    """Поиск в ElasticSearch по группам."""
    all_hits = []
    client = Elasticsearch()
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
    return all_hits


def count_obj_types_filtered(all_hits, res_obj_types, filter_obj_state):
    """Количество объектов определённых типов в отфильтрованных результатах."""
    if filter_obj_state:
        filtered_hits = list(
            filter(lambda x: str(x['Document']['Status']) in filter_obj_state, all_hits))
    else:
        filtered_hits = all_hits
    for obj_type in res_obj_types:
        obj_type['count'] = len(list(filter(
            lambda x: x['Document']['idObjType'] == obj_type['id'],
            filtered_hits
        )))
    return res_obj_types


def count_obj_states_filtered(all_hits, res_obj_states, filter_obj_type):
    """Количество объектов определённых статусов в отфильтрованных результатах."""
    if filter_obj_type:
        filtered_hits = list(filter(lambda x: str(x['Document']['idObjType']) in filter_obj_type, all_hits))
    else:
        filtered_hits = all_hits
    for obj_state in res_obj_states:
        obj_state['count'] = len(list(filter(
            lambda x: x['Document']['Status'] == obj_state['obj_state'],
            filtered_hits
        )))
    return res_obj_states
