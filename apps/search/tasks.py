from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from celery import shared_task
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core import management
from django.utils.translation import gettext as _
from django.db.models import F
from django_celery_results.models import TaskResult
from django.utils.timezone import now
from .models import SimpleSearchField, AppDocuments, ObjType, IpcAppList, OrderService
from .utils import (prepare_query, sort_results, filter_results, extend_doc_flow, get_search_groups,
                    get_elastic_results, get_search_in_transactions, get_transactions_types, get_completed_order,
                    create_selection_inv_um_ld, get_data_for_selection_tm, create_selection_tm,
                    prepare_data_for_search_report, create_search_res_doc, sort_doc_flow,
                    filter_app_data, filter_bad_apps)
from .dataclasses import ServiceExecuteResult, ServiceExecuteResultError
from apps.search.services.reports import ReportWriterDocxCreator
from uma.utils import get_unique_filename, get_user_or_anonymous
from .forms import AdvancedSearchForm, SimpleSearchForm, get_search_form
import apps.search.services as search_services
import os
import json
import time
import dataclasses
from zipfile import ZipFile
from pathlib import Path
from datetime import timedelta
from typing import List


@shared_task
def perform_simple_search(user_id, get_params):
    """Задача для выполнения простого поиска."""
    formset = get_search_form('simple', get_params)
    # Валидация запроса
    try:
        if not formset.is_valid():
            errors = []
            errors.extend(formset.errors)
            errors.extend(formset.non_form_errors())
            return {
                'validation_errors': errors,
                'get_params': get_params
            }
    except ValidationError:
        return {
            'validation_errors': _('Некоректні умови пошуку'),
            'get_params': get_params
        }

    # Формирование поискового запроса ElasticSearch
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

    # Пользователь
    user = get_user_or_anonymous(user_id)

    qs = None
    for s in formset.cleaned_data:
        if s:
            elastic_field = SimpleSearchField.objects.get(pk=s['param_type']).elastic_index_field
            if elastic_field:
                query = prepare_query(s['value'], elastic_field)

                if elastic_field.field_type == 'text':
                    fields = [
                        f"{elastic_field.field_name}^2",
                        f"{elastic_field.field_name}.exact^3",
                        f"{elastic_field.field_name}.*",
                    ]
                else:
                    fields = [
                        f"{elastic_field.field_name}",
                    ]

                q = Q(
                    'query_string',
                    query=query,
                    fields=fields,
                    quote_field_suffix=".exact",
                    default_operator='AND'
                )

                # Nested тип
                if elastic_field.parent:
                    q = Q(
                        'nested',
                        path=elastic_field.parent.field_name,
                        query=q,
                    )

                if qs is not None:
                    qs &= q
                else:
                    qs = q

    # Не включать в список результатов заявки, по которым выдан патент
    qs = filter_bad_apps(qs)

    s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(qs).source(
        excludes=["*.DocBarCode", "*.DOCBARCODE"]
    )

    # Сортировка
    if get_params.get('sort_by'):
        s = sort_results(s, get_params['sort_by'][0])
    else:
        s = s.sort('_score')

    # Фильтрация, агрегация
    s, aggregations = filter_results(s, get_params)

    results_on_page = int(get_params.get('show', [10])[0])
    if results_on_page > 100:
        results_on_page = 100
    elif results_on_page < 10:
        results_on_page = 10
    res_from = results_on_page * (int(get_params['page'][0]) - 1) if get_params.get('page') else 0
    res_to = res_from + results_on_page
    items = []
    for i in s[res_from:res_to]:
        item = i.to_dict()
        item['meta'] = i.meta.to_dict()
        items.append(filter_app_data(item, user))
    results = {
        'items': items,
        'total': s.count()
    }

    return {
        'aggregations': aggregations,
        'results': results,
        'get_params': get_params
    }


@shared_task(expires=10)
def validate_query(get_params):
    """Задача для выполнения валидации запрсоа на поиск средствами ElasticSearch."""
    for key, value in get_params.items():
        if len(value) == 1 and key not in ('obj_state', 'obj_type'):
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
def get_app_details(id_app_number: int, user_id: int) -> dict:
    """Задача для получения деталей по заявке."""
    hit = search_services.application_get_app_elasticsearch_data(id_app_number)
    if not hit:
        return {}

    user = get_user_or_anonymous(user_id)

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

        if 'DOCFLOW' in hit and 'DOCUMENTS' in hit['DOCFLOW']:
            hit['DOCFLOW']['DOCUMENTS'] = search_services.application_filter_documents_im_um_ld(
                hit['biblio_data'],
                hit['DOCFLOW']['DOCUMENTS']
            )

    elif hit['Document']['idObjType'] == 4:
        hit['TradeMark']['TrademarkDetails'] = search_services.application_prepare_biblio_data_tm(
            hit['TradeMark']['TrademarkDetails'],
            search_services.application_get_app_db_data(id_app_number)
        )
        if hit['TradeMark'].get('DocFlow', {}).get('Documents'):
            hit['TradeMark']['DocFlow']['Documents'] = search_services.application_filter_documents_tm_id(
                hit['TradeMark'].get('DocFlow', {}).get('Documents', [])
            )

    elif hit['Document']['idObjType'] == 6:
        hit['Design']['DesignDetails'] = search_services.application_prepare_biblio_data_id(
            hit['Design']['DesignDetails']
        )
        if hit['Design'].get('DocFlow', {}).get('Documents'):
            hit['Design']['DocFlow']['Documents'] = search_services.application_filter_documents_tm_id(
                hit['Design'].get('DocFlow', {}).get('Documents', [])
            )

    # Сортировка документов заявки по дате
    sort_doc_flow(hit)

    # Сортировка оповещений
    if hit['search_data']['obj_state'] == 2:
        search_services.application_sort_transactions(hit)

    hit['meta'] = {'id': id_app_number}

    return filter_app_data(hit, user)


@shared_task
def perform_advanced_search(user_id, get_params):
    """Задача для выполнения расширенного поиска."""
    formset = get_search_form('advanced', get_params)
    # Валидация запроса
    try:
        if not formset.is_valid():
            errors = []
            errors.extend(formset.errors)
            errors.extend(formset.non_form_errors())
            return {
                'validation_errors': errors,
                'get_params': get_params
            }
    except ValidationError:
        return {
            'validation_errors': _('Некоректні умови пошуку'),
            'get_params': get_params
        }

    # Разбивка поисковых данных на поисковые группы
    search_groups = get_search_groups(formset.cleaned_data)

    # Пользователь
    user = get_user_or_anonymous(user_id)

    # Поиск в ElasticSearch по каждой группе
    s = get_elastic_results(search_groups)

    # Сортировка
    if get_params.get('sort_by'):
        s = sort_results(s, get_params['sort_by'][0])
    else:
        s = s.sort('_score')

    # Фильтрация, агрегация
    s, aggregations = filter_results(s, get_params)

    # Пагинация
    results_on_page = int(get_params.get('show', [10])[0])
    if results_on_page > 100:
        results_on_page = 100
    elif results_on_page < 10:
        results_on_page = 10
    res_from = results_on_page * (int(get_params['page'][0]) - 1) if get_params.get('page') else 0
    res_to = res_from + results_on_page
    items = []
    for i in s[res_from:res_to]:
        item = i.to_dict()
        item['meta'] = i.meta.to_dict()
        items.append(filter_app_data(item, user))
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
def perform_transactions_search(get_params):
    """Выполняет поиск в транзациях"""
    form = get_search_form('transactions', get_params)
    # Валидация запроса
    try:
        if not form.is_valid():
            return {
                'validation_errors': form.errors,
                'get_params': get_params
            }
    except ValidationError:
        return {
            'validation_errors': _('Некоректні умови пошуку'),
            'get_params': get_params
        }

    s = get_search_in_transactions(form.cleaned_data)

    # Сортировка
    if get_params.get('sort_by'):
        s = sort_results(s, get_params['sort_by'][0])
    else:
        s = s.sort('_score')

    # Фильтрация, агрегация
    s, aggregations = filter_results(s, get_params)

    # Пагинация
    results_on_page = int(get_params.get('show', [10])[0])
    if results_on_page > 100:
        results_on_page = 100
    elif results_on_page < 10:
        results_on_page = 10
    res_from = results_on_page * (int(get_params['page'][0]) - 1) if get_params.get('page') else 0
    res_to = res_from + results_on_page
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
        ObjType.objects.exclude(
            pk__in=(9, 10, 11, 12, 13, 14)
        ).order_by('id').annotate(value=F(f"obj_type_{lang_code}")).values('id', 'value')
    )

    # Типы оповещений
    for obj_type in obj_types:
        obj_type['transactions_types'] = get_transactions_types(obj_type['id'])

    return obj_types


@shared_task
def perform_favorites_search(favorites_ids, user_id, get_params):
    """Задача для выполнения простого поиска."""
    # Формирование поискового запроса ElasticSearch
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

    # Пользователь
    user = get_user_or_anonymous(user_id)

    q = Q(
        'bool',
        must=[Q('terms', _id=favorites_ids)],
    )
    s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).source(
        excludes=["*.DocBarCode", "*.DOCBARCODE"]
    ).query(q)

    # Сортировка
    if get_params.get('sort_by'):
        s = sort_results(s, get_params['sort_by'][0])
    else:
        s = s.sort('_score')

    # Пагинация
    results_on_page = int(get_params.get('show', [10])[0])
    if results_on_page > 100:
        results_on_page = 100
    elif results_on_page < 10:
        results_on_page = 10
    res_from = results_on_page * (int(get_params['page'][0]) - 1) if get_params.get('page') else 0
    res_to = res_from + results_on_page
    items = []
    for i in s[res_from:res_to]:
        item = i.to_dict()
        item['meta'] = i.meta.to_dict()
        items.append(filter_app_data(item, user))
    results = {
        'items': items,
        'total': s.count()
    }

    return {
        'results': results,
        'get_params': get_params
    }


@shared_task
def get_order_documents(user_id: int, id_app_number: int, id_cead_doc: int | List[int], ip_user: str,
                        lang_code: str) -> str:
    """Возвращает название файла документа или архива с документами, заказанного(ых) через "стол заказов"."""
    if isinstance(id_cead_doc, int):
        id_cead_doc = [id_cead_doc]
    download_service = search_services.DownloadDocumentsService()
    res = download_service.execute(id_cead_doc, id_app_number, user_id, ip_user, lang_code)
    return json.dumps(dataclasses.asdict(res))


@shared_task
def create_selection(id_app_number, user_id, user_ip, get_data):
    """Возвращает url файла документа с выпиской по заявке."""
    try:
        app = IpcAppList.objects.get(id=id_app_number, registration_number__gt=0)
    except IpcAppList.DoesNotExist:
        return False

    # Каталог с выписками пользователя
    directory_path = os.path.join(
        settings.ORDERS_ROOT,
        str(user_id),
        'selections',
        str(id_app_number)
    )
    os.makedirs(directory_path, exist_ok=True)
    # Файл с выпиской
    file_path = os.path.join(directory_path, f"{id_app_number}.docx")

    # Изобретения, полезные модели, топографии
    if app.obj_type_id in (1, 2, 3):
        # Создание заказа
        order = OrderService(
            user_id=user_id,
            ip_user=user_ip,
            app_id=id_app_number,
            create_external_documents=1,
            externaldoc_enternum=270,
            order_completed=False
        )
        order.save()

        # Проверка обработан ли заказ
        order = get_completed_order(order.id)

        if order:
            # Формирование выписки и сохранение её на диск
            create_selection_inv_um_ld(json.loads(order.external_doc_body), get_data, file_path)
        else:
            return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))

    # Знаки для товаров и услуг
    elif app.obj_type_id == 4:
        client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        q = Q('match', _id=id_app_number)
        s = Search(index=settings.ELASTIC_INDEX_NAME).using(client).query(q).execute()
        if s:
            hit = s[0]
            data = get_data_for_selection_tm(hit)
            # Формирование выписки и сохранение её на диск
            create_selection_tm(data, get_data, file_path)
        else:
            return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))
    else:
        return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))

    # Возврат url сформированного файла с выпиской
    return json.dumps(
        dataclasses.asdict(
            ServiceExecuteResult(
                status='success',
                data={
                    'file_path': os.path.join(
                        settings.MEDIA_URL,
                        'OrderService',
                        str(user_id),
                        'selections',
                        str(id_app_number),
                        f"{id_app_number}.docx"
                    )
                }
            )
        )
    )


@shared_task
def create_simple_search_results_file_docx(user_id, get_params, lang_code):
    """Возвращает url файла с результатами простого поиска (docx)."""
    formset = get_search_form('simple', get_params)
    # Валидация запроса
    if formset.is_valid():
        client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        user = get_user_or_anonymous(user_id)
        qs = None
        for s in formset.cleaned_data:
            elastic_field = SimpleSearchField.objects.get(pk=s['param_type']).elastic_index_field
            if elastic_field:
                query = prepare_query(s['value'], elastic_field)

                if elastic_field.field_type == 'text':
                    fields = [
                        f"{elastic_field.field_name}^2",
                        f"{elastic_field.field_name}.exact^3",
                        f"{elastic_field.field_name}.*",
                    ]
                else:
                    fields = [
                        f"{elastic_field.field_name}",
                    ]

                q = Q(
                    'query_string',
                    query=query,
                    fields=fields,
                    quote_field_suffix=".exact",
                    default_operator='AND'
                )

                # Nested тип
                if elastic_field.parent:
                    q = Q(
                        'nested',
                        path=elastic_field.parent.field_name,
                        query=q,
                    )

                if qs is not None:
                    qs &= q
                else:
                    qs = q

        qs = filter_bad_apps(qs)

        s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(qs)

        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        # Фильтрация
        # Возможные фильтры
        filters = [
            {
                'title': 'obj_type',
                'field': 'Document.idObjType'
            },
            {
                'title': 'obj_state',
                'field': 'search_data.obj_state'
            },
            {
                'title': 'registration_status_color',
                'field': 'search_data.registration_status_color'
            },
        ]

        for item in filters:
            if get_params.get(f"filter_{item['title']}"):
                # Фильтрация в основном запросе
                s = s.filter('terms', **{item['field']: get_params.get(f"filter_{item['title']}")})

        if s.count() <= 500:
            # Получение заявок и фильтрация данных
            applications = []
            for application in s.params(size=1000, preserve_order=True).scan():
                res = application.to_dict()
                res['meta'] = application.meta.to_dict()
                applications.append(filter_app_data(res, user))

            directory_path = Path(settings.MEDIA_ROOT) / 'search_results'
            os.makedirs(str(directory_path), exist_ok=True)

            # Имя файла с результатами поиска
            file_name = f"{get_unique_filename('simple_search')}.docx"
            file_path = directory_path / file_name

            # Генерация отчёта
            report_writer = ReportWriterDocxCreator.create(
                applications,
                search_services.inid_code_get_list(lang_code),
                lang_code
            )
            report_writer.generate(file_path)

            # Возврат url сформированного файла с результатами поиска
            res = Path(settings.MEDIA_URL) / 'search_results' / file_name
            return json.dumps(
                dataclasses.asdict(
                    ServiceExecuteResult(
                        status='success',
                        data={'file_path': str(res)}
                    )
                )
            )
    return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))


@shared_task
def create_simple_search_results_file_xlsx(user_id, get_params, lang_code):
    """Возвращает url файла с результатами простого поиска (.xlsx)."""
    formset = get_search_form('simple', get_params)
    # Валидация запроса
    if formset.is_valid():
        client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        user = get_user_or_anonymous(user_id)
        qs = None
        for s in formset.cleaned_data:
            elastic_field = SimpleSearchField.objects.get(pk=s['param_type']).elastic_index_field
            if elastic_field:
                query = prepare_query(s['value'], elastic_field)

                if elastic_field.field_type == 'text':
                    fields = [
                        f"{elastic_field.field_name}^2",
                        f"{elastic_field.field_name}.exact^3",
                        f"{elastic_field.field_name}.*",
                    ]
                else:
                    fields = [
                        f"{elastic_field.field_name}",
                    ]

                q = Q(
                    'query_string',
                    query=query,
                    fields=fields,
                    quote_field_suffix=".exact",
                    default_operator='AND'
                )

                # Nested тип
                if elastic_field.parent:
                    q = Q(
                        'nested',
                        path=elastic_field.parent.field_name,
                        query=q,
                    )

                if qs is not None:
                    qs &= q
                else:
                    qs = q

        qs = filter_bad_apps(qs)

        s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(qs)

        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        # Фильтрация
        # Возможные фильтры
        filters = [
            {
                'title': 'obj_type',
                'field': 'Document.idObjType'
            },
            {
                'title': 'obj_state',
                'field': 'search_data.obj_state'
            },
            {
                'title': 'registration_status_color',
                'field': 'search_data.registration_status_color'
            },
        ]

        for item in filters:
            if get_params.get(f"filter_{item['title']}"):
                # Фильтрация в основном запросе
                s = s.filter('terms', **{item['field']: get_params.get(f"filter_{item['title']}")})

        if s.count() <= 500:
            s = s.source(['search_data', 'Document', 'Claim', 'Patent', 'TradeMark', 'MadridTradeMark', 'Design', 'Geo',
                          'Certificate'])

            # Данные для Excel-файла
            data = prepare_data_for_search_report(s, lang_code, user)

            directory_path = os.path.join(
                settings.MEDIA_ROOT,
                'search_results',
            )
            os.makedirs(directory_path, exist_ok=True)
            # Имя файла с результатами поиска
            file_name = f"{get_unique_filename('simple_search')}.xlsx"
            file_path = os.path.join(directory_path, file_name)

            # Формировние и сохранение Excel-файла
            create_search_res_doc(data, file_path)

            # Возврат url сформированного файла с результатами поиска
            res = os.path.join(
                settings.MEDIA_URL,
                'search_results',
                file_name
            )
            return json.dumps(
                dataclasses.asdict(
                    ServiceExecuteResult(
                        status='success',
                        data={'file_path': res}
                    )
                )
            )
    return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))


@shared_task
def create_advanced_search_results_file_docx(user_id, get_params, lang_code):
    """Возвращает url файла с результатами расширенного поиска (.docx)."""
    formset = get_search_form('advanced', get_params)
    # Валидация запроса
    if formset.is_valid():
        # Разбивка поисковых данных на поисковые группы
        search_groups = get_search_groups(formset.cleaned_data)

        # Поиск в ElasticSearch по каждой группе
        user = get_user_or_anonymous(user_id)
        s = get_elastic_results(search_groups)

        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        # Фильтрация
        # Возможные фильтры
        filters = [
            {
                'title': 'obj_type',
                'field': 'Document.idObjType'
            },
            {
                'title': 'obj_state',
                'field': 'search_data.obj_state'
            },
            {
                'title': 'registration_status_color',
                'field': 'search_data.registration_status_color'
            },
        ]

        for item in filters:
            if get_params.get(f"filter_{item['title']}"):
                # Фильтрация в основном запросе
                s = s.filter('terms', **{item['field']: get_params.get(f"filter_{item['title']}")})

        if s.count() <= 500:
            # Получение заявок и фильтрация данных
            applications = []
            for application in s.params(size=1000, preserve_order=True).scan():
                res = application.to_dict()
                res['meta'] = application.meta.to_dict()
                applications.append(filter_app_data(res, user))

            directory_path = Path(settings.MEDIA_ROOT) / 'search_results'
            os.makedirs(str(directory_path), exist_ok=True)

            # Имя файла с результатами поиска
            file_name = f"{get_unique_filename('advanced_search')}.docx"
            file_path = directory_path / file_name

            # Генерация отчёта
            report_writer = ReportWriterDocxCreator.create(
                applications,
                search_services.inid_code_get_list(lang_code),
                lang_code
            )
            report_writer.generate(file_path)

            # Возврат url сформированного файла с результатами поиска
            res = Path(settings.MEDIA_URL) / 'search_results' / file_name
            return json.dumps(
                dataclasses.asdict(
                    ServiceExecuteResult(
                        status='success',
                        data={'file_path': str(res)}
                    )
                )
            )
    return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))


@shared_task
def create_advanced_search_results_file_xlsx(user_id, get_params, lang_code):
    """Возвращает url файла с результатами расширенного поиска (.docx)."""
    formset = get_search_form('advanced', get_params)
    # Валидация запроса
    if formset.is_valid():
        # Разбивка поисковых данных на поисковые группы
        search_groups = get_search_groups(formset.cleaned_data)

        # Поиск в ElasticSearch по каждой группе
        user = get_user_or_anonymous(user_id)
        s = get_elastic_results(search_groups)

        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        # Фильтрация
        # Возможные фильтры
        filters = [
            {
                'title': 'obj_type',
                'field': 'Document.idObjType'
            },
            {
                'title': 'obj_state',
                'field': 'search_data.obj_state'
            },
            {
                'title': 'registration_status_color',
                'field': 'search_data.registration_status_color'
            },
        ]

        for item in filters:
            if get_params.get(f"filter_{item['title']}"):
                # Фильтрация в основном запросе
                s = s.filter('terms', **{item['field']: get_params.get(f"filter_{item['title']}")})

        if s.count() <= 500:
            s = s.source(['search_data', 'Document', 'Claim', 'Patent', 'TradeMark', 'MadridTradeMark', 'Design', 'Geo',
                          'Certificate'])

            # Сортировка
            if get_params.get('sort_by'):
                s = sort_results(s, get_params['sort_by'][0])
            else:
                s = s.sort('_score')

            # Данные для Excel-файла
            data = prepare_data_for_search_report(s, lang_code, user)

            directory_path = os.path.join(
                settings.MEDIA_ROOT,
                'search_results',
            )
            os.makedirs(directory_path, exist_ok=True)
            # Имя файла с результатами поиска
            file_name = f"{get_unique_filename('advanced_search')}.xlsx"
            file_path = os.path.join(directory_path, file_name)

            # Формировние и сохранение Excel-файла
            create_search_res_doc(data, file_path)

            # Возврат url сформированного файла с результатами поиска
            res = os.path.join(
                settings.MEDIA_URL,
                'search_results',
                file_name
            )
            return json.dumps(
                dataclasses.asdict(
                    ServiceExecuteResult(
                        status='success',
                        data={'file_path': res}
                    )
                )
            )
    return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))


@shared_task
def create_transactions_search_results_file_docx(get_params, lang_code):
    """Возвращает url файла с результатами поиска по оповещениям."""
    form = get_search_form('transactions', get_params)
    # Валидация запроса
    if form.is_valid():
        s = get_search_in_transactions(form.cleaned_data)

        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        if s and s.count() <= 500:
            directory_path = Path(settings.MEDIA_ROOT) / 'search_results'
            os.makedirs(str(directory_path), exist_ok=True)

            # Имя файла с результатами поиска
            file_name = f"{get_unique_filename('transactions_search')}.docx"
            file_path = directory_path / file_name

            # Генерация отчёта
            report_writer = ReportWriterDocxCreator.create(
                [x.to_dict() for x in s.params(size=1000, preserve_order=True).scan()],
                search_services.inid_code_get_list(lang_code),
                lang_code
            )
            report_writer.generate(file_path)

            # Возврат url сформированного файла с результатами поиска
            res = Path(settings.MEDIA_URL) / 'search_results' / file_name
            return json.dumps(
                dataclasses.asdict(
                    ServiceExecuteResult(
                        status='success',
                        data={'file_path': str(res)}
                    )
                )
            )
    return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))


@shared_task
def create_transactions_search_results_file_xlsx(get_params, lang_code):
    """Возвращает url файла с результатами поиска по оповещениям."""
    form = get_search_form('transactions', get_params)
    # Валидация запроса
    if form.is_valid():
        s = get_search_in_transactions(form.cleaned_data)

        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        if s and s.count() <= 500:
            s = s.source(['search_data', 'Document', 'Claim', 'Patent', 'TradeMark', 'Design', 'Geo'])

            # Сортировка
            if get_params.get('sort_by'):
                s = sort_results(s, get_params['sort_by'][0])
            else:
                s = s.sort('_score')

            # Данные для Excel-файла
            data = prepare_data_for_search_report(s, lang_code)

            directory_path = os.path.join(
                settings.MEDIA_ROOT,
                'search_results',
            )
            os.makedirs(directory_path, exist_ok=True)
            # Имя файла с результатами поиска
            file_name = f"{get_unique_filename('transactions_search')}.xlsx"
            file_path = os.path.join(directory_path, file_name)

            # Формировние и сохранение Excel-файла
            create_search_res_doc(data, file_path)

            # Возврат url сформированного файла с результатами поиска
            res = os.path.join(
                settings.MEDIA_URL,
                'search_results',
                file_name
            )
            return json.dumps(
                dataclasses.asdict(
                    ServiceExecuteResult(
                        status='success',
                        data={'file_path': res}
                    )
                )
            )
    return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))


@shared_task
def create_details_file_docx(id_app_number: int, user_id: int, lang_code: str):
    """Создаёт файл docx с библиографическими данными объекта пром. собственности."""
    hit = search_services.application_get_app_elasticsearch_data(id_app_number)
    if not hit:
        return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))
    hit['meta'] = {'id': id_app_number}

    user = get_user_or_anonymous(user_id)
    directory_path = Path(settings.MEDIA_ROOT) / 'search_results'
    os.makedirs(str(directory_path), exist_ok=True)

    # Имя файла с результатами поиска
    if hit['search_data']['app_number'] is not None:
        file_name = f"{get_unique_filename(hit['search_data']['app_number'])}.docx"
    else:
        file_name = f"{get_unique_filename(hit['search_data']['protective_doc_number'])}.docx"
    file_path = directory_path / file_name

    # Генерация отчёта
    report_writer = ReportWriterDocxCreator.create(
        [filter_app_data(hit, user)],
        search_services.inid_code_get_list(lang_code),
        lang_code
    )
    report_writer.generate(file_path)

    # Возврат url сформированного файла с результатами поиска
    res = Path(settings.MEDIA_URL) / 'search_results' / file_name
    return json.dumps(
        dataclasses.asdict(
            ServiceExecuteResult(
                status='success',
                data={'file_path': str(res)}
            )
        )
    )


@shared_task
def create_shared_docs_archive(id_app_number):
    """Возвращает url файла с архивом доступных всем документов."""
    try:
        app = IpcAppList.objects.get(id=id_app_number, registration_number__gt=0, obj_type_id__in=(1, 2, 3))
    except IpcAppList.DoesNotExist:
        return json.dumps(dataclasses.asdict(ServiceExecuteResult(status='error')))

    directory_path = os.path.join(
        settings.MEDIA_ROOT,
        'shared_docs'
    )
    os.makedirs(directory_path, exist_ok=True)
    file_name = f"{get_unique_filename(app.app_number)}.zip"
    file_path = os.path.join(
        directory_path,
        file_name
    )

    # Создание архива
    zip_ = ZipFile(file_path, "a")
    for document in app.appdocuments_set.filter(file_type='pdf').all():
        zip_.write(
            document.file_name.replace('\\\\bear\\share\\', settings.DOCUMENTS_MOUNT_FOLDER).replace('\\', '/'),
            Path(document.file_name.replace('\\', '/')).name
        )

    # fix for Linux zip files read in Windows
    for file in zip_.filelist:
        file.create_system = 0

    zip_.close()

    # Возврат url сформированного файла
    res = os.path.join(
        settings.MEDIA_URL,
        'shared_docs',
        file_name
    )
    return json.dumps(
        dataclasses.asdict(
            ServiceExecuteResult(
                status='success',
                data={'file_path': res}
            )
        )
    )


@shared_task
def clear_results_table(minutes=5):
    """Очищает таблицу django_celery_results_taskresult от записей старше minutes минут."""
    results = TaskResult.objects.filter(date_done__lte=now() - timedelta(minutes=minutes))
    TaskResult.objects.filter(pk__in=results)._raw_delete(results.db)


@shared_task
def clear_sessions():
    """Очищает просроченные сессиии пользователей."""
    management.call_command('clearsessions')


@shared_task
def clear_old_files(path, older_than_minutes=10):
    """Очищает каталог path. Удаляет файлы старше older_than_minutes минут, а затем удаляет пустые каталоги."""
    for address, dirs, files in os.walk(path):
        # Удаление старых файлов
        for file in files:
            full_path = os.path.join(address, file)
            if os.stat(full_path).st_mtime < (time.time() - older_than_minutes*60):
                os.remove(full_path)

        # Удаление пустых каталогов
        for dir_ in dirs:
            full_path = os.path.join(address, dir_)
            if not os.listdir(full_path):
                os.rmdir(full_path)
