from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from .models import ObjType, InidCodeSchedule
import re


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


def prepare_advanced_query(query, field_type):
    """Обрабатывает строку расширенного запроса пользователя."""
    if field_type == 'date':
        # Форматирование дат
        query = re.sub(r'>(\d{1,2})\.(\d{1,2})\.(\d{4})', '{\\3-\\2-\\1 TO *}', query)
        query = re.sub(r'<(\d{1,2})\.(\d{1,2})\.(\d{4})', '{* TO \\3-\\2-\\1}', query)
        query = re.sub(r'>=(\d{1,2})\.(\d{1,2})\.(\d{4})', '[\\3-\\2-\\1 TO *]', query)
        query = re.sub(r'<=(\d{1,2})\.(\d{1,2})\.(\d{4})', '[* TO \\3-\\2-\\1]', query)
        query = re.sub(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '\\3-\\2-\\1', query)
    query = query.replace(" ТА ", " AND ").replace(" АБО ", " OR ").replace(" НЕ ", " NOT ")
    return query


def prepare_simple_query(query, field_type):
    """Обрабатывает строку простого запроса пользователя."""
    if field_type == 'date':
        # Форматирование дат
        query = re.sub(r'>(\d{1,2})\.(\d{1,2})\.(\d{4})', '{\\3-\\2-\\1 TO *}', query)
        query = re.sub(r'<(\d{1,2})\.(\d{1,2})\.(\d{4})', '{* TO \\3-\\2-\\1}', query)
        query = re.sub(r'>=(\d{1,2})\.(\d{1,2})\.(\d{4})', '[\\3-\\2-\\1 TO *]', query)
        query = re.sub(r'<=(\d{1,2})\.(\d{1,2})\.(\d{4})', '[* TO \\3-\\2-\\1]', query)
        query = re.sub(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '\\3-\\2-\\1', query)
    return query


def elastic_search_groups(search_groups):
    """Поиск в ElasticSearch по группам."""
    all_hits = []
    client = Elasticsearch()
    for group in search_groups:
        if group['search_params']:
            # Идентификаторы schedule_type для заявок или охранных документов
            schedule_type_ids = (10, 11, 12, 13, 14, 15) if group['obj_state'] == 1 else (3, 4, 5, 6, 7, 8)

            qs = Q('query_string', query=f"{group['obj_type'].pk}", default_field='Document.idObjType')
            qs &= Q('query_string', query=f"{group['obj_state']}", default_field='search_data.obj_state')
            # TODO: для всех показывать только статусы 3 и 4, для вип-ролей - всё.
            #qs &= Q('query_string', query="3 OR 4", default_field='Document.Status')

            for search_param in group['search_params']:
                # Поле поиска ElasticSearch
                inid_schedule = InidCodeSchedule.objects.filter(
                    ipc_code__id=search_param['ipc_code'],
                    schedule_type__obj_type=group['obj_type'],
                    schedule_type__id__in=schedule_type_ids
                ).first()

                # Проверка доступно ли поле для поиска
                if inid_schedule.enable_search and inid_schedule.elastic_index_field is not None:
                    qs &= Q(
                        'query_string',
                        query=f"{prepare_advanced_query(search_param['value'], inid_schedule.elastic_index_field.field_type)}",
                        default_field=inid_schedule.elastic_index_field.field_name,
                        analyze_wildcard=True
                    )
            s = Search(using=client, index="uma").query(qs)
            # total = s.count()
            s = s[0:500]
            group['response'] = s.execute()
            # Объединение результатов поиска
            for hit in group['response']:
                all_hits.append(hit)
    return all_hits


def count_obj_types_filtered(all_hits, res_obj_types, filter_obj_state):
    """Количество объектов определённых типов в отфильтрованных результатах."""
    if filter_obj_state:
        filtered_hits = list(
            filter(lambda x: str(x['search_data']['obj_state']) in filter_obj_state, all_hits))
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
            lambda x: x['search_data']['obj_state'] == obj_state['obj_state'],
            filtered_hits
        )))
    return res_obj_states


def get_client_ip(request):
    """Возвращает IP-адрес пользователя."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ResultsProxy(object):
    """
    A proxy object for returning Elasticsearch results that is able to be
    passed to a Paginator.
    """
    def __init__(self, s):
        self.s = s

    def __len__(self):
        return self.s.count()

    def __getitem__(self, item):
        return self.s[item.start:item.stop].execute()
