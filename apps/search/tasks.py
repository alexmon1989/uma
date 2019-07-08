from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.db.models import F
from .models import SimpleSearchField, AppDocuments, ObjType
from .utils import (prepare_simple_query, filter_bad_apps, filter_unpublished_apps, sort_results, filter_results,
                    extend_doc_flow, get_search_groups, get_elastic_results, get_search_in_transactions,
                    get_transactions_types)
from .forms import AdvancedSearchForm, SimpleSearchForm


@shared_task
def perform_simple_search(cleaned_data, user_id, get_params):
    """Задача для выполнения простого поиска."""
    # Формирование поискового запроса ElasticSearch
    client = Elasticsearch(settings.ELASTIC_HOST)
    qs = None
    for s in cleaned_data:
        elastic_field = SimpleSearchField.objects.get(pk=s['param_type']).elastic_index_field
        if elastic_field:
            q = Q(
                'query_string',
                query=prepare_simple_query(s['value'], elastic_field.field_type),
                default_field=elastic_field.field_name,
                default_operator='AND'
            )
            if qs is not None:
                qs &= q
            else:
                qs = q

    if qs is not None:
        # Не показывать заявки, по которым выдан охранный документ
        qs = filter_bad_apps(qs)

        # Не показывать неопубликованные заявки
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            user = AnonymousUser()
        qs = filter_unpublished_apps(user, qs)

    s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(qs)

    # Сортировка
    if get_params.get('sort_by'):
        s = sort_results(s, get_params['sort_by'][0])
    else:
        s = s.sort('_score')

    # Фильтрация, агрегация
    s, aggregations = filter_results(s, get_params)

    res_from = 10 * (int(get_params['page'][0]) - 1) if get_params.get('page') else 0
    res_to = res_from + 10
    items = []
    for i in s[res_from:res_to]:
        item = i.to_dict()
        item['meta'] = i.meta.to_dict()
        items.append(item)
    results = {
        'items': items,
        'total': s.count()
    }

    return {
        'aggregations': aggregations,
        'results': results,
        'get_params': get_params
    }


@shared_task
def validate_query(get_params):
    """Задача для выполнения валидации запрсоа на поиск средствами ElasticSearch."""
    for key, value in get_params.items():
        if len(value) == 1 and key != 'obj_state':
            get_params[key] = value[0]
    search_type = get_params.get('search_type')
    if search_type == 'simple':
        form = SimpleSearchForm(get_params)
    elif search_type == 'advanced':
        form = AdvancedSearchForm(get_params)
    else:
        return False

    return form.is_valid()


@shared_task
def get_app_details(id_app_number, user_id):
    """Задача для получения деталей по заявке."""
    client = Elasticsearch(settings.ELASTIC_HOST)
    q = Q(
        'bool',
        must=[Q('match', _id=id_app_number)],
    )
    q = filter_bad_apps(q)  # Исключение заявок, не пригодных к отображению
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = AnonymousUser()
    # Фильтр заявок, которые не положено публиковать в интернет
    q = filter_unpublished_apps(user, q)

    s = Search().using(client).query(q).execute()
    if not s:
        return {}
    hit = s[0].to_dict()

    if hit['Document']['idObjType'] in (1, 2, 3):
        hit['biblio_data'] = hit['Claim'] if hit['search_data']['obj_state'] == 1 else hit['Patent']

        # Оповещения
        transactions = hit.get('TRANSACTIONS', {}).get('TRANSACTION', [])
        if type(transactions) is dict:
            transactions = [transactions]
        hit['transactions'] = transactions

        # Документы заявки (библиографические)
        hit['biblio_documents'] = AppDocuments.get_app_documents(id_app_number)

        # Если это патент, то необходимо объеденить документы, платежи и т.д. с теми которые были на этапе заявки
        if hit['search_data']['obj_state'] == 2:
             extend_doc_flow(hit)

    hit['id_app_number'] = id_app_number

    return hit


@shared_task
def perform_advanced_search(cleaned_data, user_id, get_params):
    """Задача для выполнения расширенного поиска."""
    # Получение пользователя
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = AnonymousUser()

    # Разбивка поисковых данных на поисковые группы
    search_groups = get_search_groups(cleaned_data)

    # Поиск в ElasticSearch по каждой группе
    s = get_elastic_results(search_groups, user)

    # Сортировка
    if get_params.get('sort_by'):
        s = sort_results(s, get_params['sort_by'][0])
    else:
        s = s.sort('_score')

    # Фильтрация, агрегация
    s, aggregations = filter_results(s, get_params)

    # Пагинация
    res_from = 10 * (int(get_params['page'][0]) - 1) if get_params.get('page') else 0
    res_to = res_from + 10
    items = []
    for i in s[res_from:res_to]:
        item = i.to_dict()
        item['meta'] = i.meta.to_dict()
        items.append(item)
    results = {
        'items': items,
        'total': s.count()
    }

    return {
        'aggregations': aggregations,
        'results': results,
        'get_params': get_params
    }


@shared_task
def perform_transactions_search(cleaned_data, get_params):
    """Выполняет поиск в транзациях"""
    s = get_search_in_transactions(cleaned_data)

    # Сортировка
    if get_params.get('sort_by'):
        s = sort_results(s, get_params['sort_by'][0])
    else:
        s = s.sort('_score')

    # Фильтрация, агрегация
    s, aggregations = filter_results(s, get_params)

    # Пагинация
    res_from = 10 * (int(get_params['page'][0]) - 1) if get_params.get('page') else 0
    res_to = res_from + 10
    items = []
    for i in s[res_from:res_to]:
        item = i.to_dict()
        item['meta'] = i.meta.to_dict()
        items.append(item)
    results = {
        'items': items,
        'total': s.count()
    }

    return {
        'aggregations': aggregations,
        'results': results,
        'get_params': get_params
    }


@shared_task
def get_obj_types_with_transactions(lang_code):
    """Возвращает типы объектов вместе с типами оповещений."""
    obj_types = list(
        ObjType.objects.order_by('id').annotate(value=F(f"obj_type_{lang_code}")).values('id', 'value')
    )

    # Типы оповещений
    for obj_type in obj_types:
        obj_type['transactions_types'] = get_transactions_types(obj_type['id'])

    return obj_types
