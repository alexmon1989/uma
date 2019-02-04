from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A
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
        query = re.sub(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '\\3-\\2-\\1', query)
    query = query.replace(" ТА ", " AND ").replace(" АБО ", " OR ").replace(" НЕ ", " NOT ")
    return query


def prepare_simple_query(query, field_type):
    """Обрабатывает строку простого запроса пользователя."""
    if field_type == 'date':
        # Форматирование дат
        query = re.sub(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '\\3-\\2-\\1', query)
    return query


def get_elastic_results(search_groups):
    """Поиск в ElasticSearch по группам."""
    qs_list = []
    for group in search_groups:
        if group['search_params']:
            # Идентификаторы schedule_type для заявок или охранных документов
            schedule_type_ids = (10, 11, 12, 13, 14, 15) if group['obj_state'] == 1 else (3, 4, 5, 6, 7, 8)
            qs = None

            for search_param in group['search_params']:
                # Поле поиска ElasticSearch
                inid_schedule = InidCodeSchedule.objects.filter(
                    ipc_code__id=search_param['ipc_code'],
                    schedule_type__obj_type=group['obj_type'],
                    schedule_type__id__in=schedule_type_ids
                ).first()

                # Проверка доступно ли поле для поиска
                if inid_schedule.enable_search and inid_schedule.elastic_index_field is not None:
                    q = Q(
                        'query_string',
                        query=f"{prepare_advanced_query(search_param['value'], inid_schedule.elastic_index_field.field_type)}",
                        default_field=inid_schedule.elastic_index_field.field_name,
                        analyze_wildcard=True
                    )
                    if not qs:
                        qs = q
                    else:
                        qs &= q

            if qs is not None:
                qs &= Q('query_string', query=f"{group['obj_type'].pk}", default_field='Document.idObjType')
                qs &= Q('query_string', query=f"{group['obj_state']}", default_field='search_data.obj_state')
                # Не показывать заявки, по которым выдан охранный документ
                qs &= ~Q('query_string', query="Document.Status:3 AND search_data.obj_state:1")

                # TODO: для всех показывать только статусы 3 и 4, для вип-ролей - всё.
                # qs &= Q('query_string', query="3 OR 4", default_field='Document.Status')

                qs_list.append(qs)

    # Формирование результирующего запроса
    qs_result = None
    for qs in qs_list:
        if qs_result is None:
            qs_result = qs
        else:
            qs_result |= qs

    client = Elasticsearch(settings.ELASTIC_HOST)
    s = Search(using=client, index="uma").query(qs_result).sort('_score')

    return s


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


def paginate_results(s, page, paginate_by=10):
    """Пагинатор для результов запроса ElasticSearch"""
    paginator = Paginator(ResultsProxy(s), paginate_by)
    page_number = page
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page


def filter_results(s, request):
    """Фильтрует результат запроса ElasticSearch И выполняет агрегацию для фильтров в сайдбаре."""
    # Агрегация для определения всех типов объектов и состояний
    s.aggs.bucket('idObjType_terms', A('terms', field='Document.idObjType'))
    s.aggs.bucket('obj_state_terms', A('terms', field='search_data.obj_state'))
    aggregations = s.execute().aggregations.to_dict()
    s_ = s

    # Фильтрация
    if request.GET.get('filter_obj_type'):
        # Фильтрация в основном запросе
        s = s.filter('terms', Document__idObjType=request.GET.getlist('filter_obj_type'))
        # Агрегация для определения количества объектов определённых типов после применения одного фильтра
        s_filter_obj_type = s_.filter(
            'terms',
            Document__idObjType=request.GET.getlist('filter_obj_type')
        )
        s_filter_obj_type.aggs.bucket('obj_state_terms', A('terms', field='search_data.obj_state'))
        aggregations_obj_state = s_filter_obj_type.execute().aggregations.to_dict()
        for bucket in aggregations['obj_state_terms']['buckets']:
            if not list(filter(lambda x: x['key'] == bucket['key'],
                               aggregations_obj_state['obj_state_terms']['buckets'])):
                aggregations_obj_state['obj_state_terms']['buckets'].append(
                    {'key': bucket['key'], 'doc_count': 0}
                )
        aggregations['obj_state_terms']['buckets'] = aggregations_obj_state['obj_state_terms']['buckets']

    if request.GET.get('filter_obj_state'):
        # Фильтрация в основном запросе
        s = s.filter('terms', search_data__obj_state=request.GET.getlist('filter_obj_state'))
        # Агрегация для определения количества объектов определённых состояний
        # после применения одного фильтра
        s_filter_obj_state = s_.filter(
            'terms',
            search_data__obj_state=request.GET.getlist('filter_obj_state')
        )
        s_filter_obj_state.aggs.bucket('idObjType_terms', A('terms', field='Document.idObjType'))
        aggregations_id_obj_type = s_filter_obj_state.execute().aggregations.to_dict()
        for bucket in aggregations['idObjType_terms']['buckets']:
            if not list(filter(lambda x: x['key'] == bucket['key'],
                               aggregations_id_obj_type['idObjType_terms']['buckets'])):
                aggregations_id_obj_type['idObjType_terms']['buckets'].append(
                    {'key': bucket['key'], 'doc_count': 0}
                )
        aggregations['idObjType_terms']['buckets'] = aggregations_id_obj_type['idObjType_terms']['buckets']

    return s, aggregations


def extend_doc_flow(hit):
    """Расширяет секцию DOCFLOW патента документами заявки"""
    # Получение заявки охранного документа
    q = Q(
        'bool',
        must=[
            Q('match', search_data__app_number=hit.search_data.app_number),
            Q('match', search_data__obj_state=1)
        ]
    )
    client = Elasticsearch(settings.ELASTIC_HOST)
    application = Search().using(client).query(q).execute()
    if application:
        application = application[0]

        try:
            # Объединение стадий
            stages = application.DOCFLOW.STAGES
            stages.extend(hit.DOCFLOW.STAGES)
            hit.DOCFLOW.STAGES = stages
        except AttributeError:
            pass

        try:
            # Объединение документов
            documents = application.DOCFLOW.DOCUMENTS
            documents.extend(hit.DOCFLOW.DOCUMENTS)
            hit.DOCFLOW.DOCUMENTS = documents
        except AttributeError:
            pass

        try:
            # Объединение платежей
            payments = application.DOCFLOW.PAYMENTS
            payments.extend(hit.DOCFLOW.PAYMENTS)
            hit.DOCFLOW.PAYMENTS = payments
        except AttributeError:
            pass

        try:
            # Объединение сборов
            collections = application.DOCFLOW.COLLECTIONS
            collections.extend(hit.DOCFLOW.COLLECTIONS)
            hit.DOCFLOW.COLLECTIONS = collections
        except AttributeError:
            pass
