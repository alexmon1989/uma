from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from celery import shared_task
from django.conf import settings
from django.db.models import F
from .models import SimpleSearchField, AppDocuments, ObjType, IpcAppList, OrderService
from .utils import (prepare_simple_query, filter_bad_apps, filter_unpublished_apps, sort_results, filter_results,
                    extend_doc_flow, get_search_groups, get_elastic_results, get_search_in_transactions,
                    get_transactions_types, get_completed_order, create_selection_inv_um_ld, get_data_for_selection_tm,
                    create_selection_tm, prepare_data_for_search_report, create_search_res_doc, user_has_access_to_docs)
from uma.utils import get_unique_filename, get_user_or_anonymous
from .forms import AdvancedSearchForm, SimpleSearchForm, get_search_form
import os
import json
from zipfile import ZipFile
from pathlib import Path


@shared_task
def perform_simple_search(user_id, get_params):
    """Задача для выполнения простого поиска."""
    formset = get_search_form('simple', get_params)
    # Валидация запроса
    if not formset.is_valid():
        return {
            'validation_errors': formset.errors,
            'get_params': get_params
        }

    # Формирование поискового запроса ElasticSearch
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    qs = None
    for s in formset.cleaned_data:
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
        qs = filter_unpublished_apps(get_user_or_anonymous(user_id), qs)

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
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    q = Q(
        'bool',
        must=[Q('match', _id=id_app_number)],
    )
    q = filter_bad_apps(q)  # Исключение заявок, не пригодных к отображению
    # Фильтр заявок, которые не положено публиковать в интернет
    q = filter_unpublished_apps(get_user_or_anonymous(user_id), q)

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
def perform_advanced_search(user_id, get_params):
    """Задача для выполнения расширенного поиска."""
    formset = get_search_form('advanced', get_params)
    # Валидация запроса
    if not formset.is_valid():
        return {
            'validation_errors': formset.errors,
            'get_params': get_params
        }

    # Разбивка поисковых данных на поисковые группы
    search_groups = get_search_groups(formset.cleaned_data)

    # Поиск в ElasticSearch по каждой группе
    s = get_elastic_results(search_groups, get_user_or_anonymous(user_id))

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
def perform_transactions_search(get_params):
    """Выполняет поиск в транзациях"""
    form = get_search_form('transactions', get_params)
    # Валидация запроса
    if not form.is_valid():
        return {
            'validation_errors': form.errors,
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


@shared_task
def get_order_documents(user_id, order_id):
    """Возвращает название файла документа или архива с документами, заказанного(ых) через "стол заказов"."""
    # Получение обработанного заказа
    order = get_completed_order(order_id)

    # Получение документа (заявки) из ElasticSearch
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    q = Q(
        'bool',
        must=[Q('match', _id=order.app_id)],
    )
    q = filter_bad_apps(q)  # Исключение заявок, не пригодных к отображению
    # Фильтр заявок, которые не положено публиковать в интернет
    user = get_user_or_anonymous(user_id)
    q = filter_unpublished_apps(user, q)

    s = Search().using(client).query(q).source(['search_data']).execute()
    if not s:
        return {}
    hit = s[0].to_dict()

    if order and user_has_access_to_docs(user, hit):
        # В зависимости от того сколько документов содержит заказ, возвращается путь к файлу или к архиву с файлами
        if order.orderdocument_set.count() == 1:
            doc = order.orderdocument_set.first()
            # Путь к файлу
            file_path = os.path.join(
                settings.MEDIA_URL,
                'OrderService',
                str(order.user_id),
                str(order.id),
                doc.file_name
            )
            return file_path
        else:
            file_path_zip = os.path.join(
                settings.ORDERS_ROOT,
                str(order.user_id),
                str(order.id),
                'docs.zip'
            )
            with ZipFile(file_path_zip, 'w') as zip_:
                for document in order.orderdocument_set.all():
                    zip_.write(
                        os.path.join(
                            settings.DOCUMENTS_MOUNT_FOLDER,
                            'OrderService',
                            str(order.user_id),
                            str(order.id),
                            document.file_name),
                        f"{document.file_name}"
                    )
            return os.path.join(
                settings.MEDIA_URL,
                'OrderService',
                str(order.user_id),
                str(order.id),
                'docs.zip'
            )

    return False


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
            return False

    # Знаки для товаров и услуг
    elif app.obj_type_id == 4:
        client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        q = Q('match', _id=id_app_number)
        s = Search().using(client).query(q).execute()
        if s:
            hit = s[0]
            data = get_data_for_selection_tm(hit)
            # Формирование выписки и сохранение её на диск
            create_selection_tm(data, get_data, file_path)
        else:
            return False
    else:
        return False

    # Возврат url сформированного файла с выпиской
    return os.path.join(
        settings.MEDIA_URL,
        'OrderService',
        str(user_id),
        'selections',
        str(id_app_number),
        f"{id_app_number}.docx"
    )


@shared_task
def create_simple_search_results_file(user_id, get_params, lang_code):
    """Возвращает url файла с результатами простого поиска."""
    formset = get_search_form('simple', get_params)
    # Валидация запроса
    if formset.is_valid():
        client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        qs = None
        for s in formset.cleaned_data:
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
            qs = filter_unpublished_apps(get_user_or_anonymous(user_id), qs)

        s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(qs)

        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        # Фильтрация
        if get_params.get('filter_obj_type'):
            # Фильтрация по типу объекта
            s = s.filter('terms', Document__idObjType=get_params.get('filter_obj_type'))

        if get_params.get('filter_obj_state'):
            # Фильтрация по статусу объекта
            s = s.filter('terms', search_data__obj_state=get_params.get('filter_obj_state'))

        if s.count() <= 5000:
            s = s.source(['search_data', 'Document'])

            # Данные для Excel-файла
            data = prepare_data_for_search_report(s, lang_code)

            # Формировние Excel-файла
            workbook = create_search_res_doc(data)

            directory_path = os.path.join(
                settings.MEDIA_ROOT,
                'search_results',
            )
            os.makedirs(directory_path, exist_ok=True)
            # Имя файла с результатами поиска
            file_name = f"{get_unique_filename('simple_search')}.xls"
            file_path = os.path.join(directory_path, file_name)

            # Сохранение файла
            workbook.save(file_path)

            # Возврат url сформированного файла с результатами поиска
            return os.path.join(
                settings.MEDIA_URL,
                'search_results',
                file_name
            )
    return False


@shared_task
def create_advanced_search_results_file(user_id, get_params, lang_code):
    """Возвращает url файла с результатами расширенного поиска."""
    formset = get_search_form('advanced', get_params)
    # Валидация запроса
    if formset.is_valid():
        # Разбивка поисковых данных на поисковые группы
        search_groups = get_search_groups(formset.cleaned_data)

        # Поиск в ElasticSearch по каждой группе
        s = get_elastic_results(search_groups, get_user_or_anonymous(user_id))

        # Фильтрация
        if get_params.get('filter_obj_type'):
            # Фильтрация по типу объекта
            s = s.filter('terms', Document__idObjType=get_params.get('filter_obj_type'))
        if get_params.get('filter_obj_state'):
            # Фильтрация по статусу объекта
            s = s.filter('terms', search_data__obj_state=get_params.get('filter_obj_state'))

        if s.count() <= 5000:
            s = s.source(['search_data', 'Document'])

            # Сортировка
            if get_params.get('sort_by'):
                s = sort_results(s, get_params['sort_by'])
            else:
                s = s.sort('_score')

            # Данные для Excel-файла
            data = prepare_data_for_search_report(s, lang_code)

            # Формировние Excel-файла
            workbook = create_search_res_doc(data)

            directory_path = os.path.join(
                settings.MEDIA_ROOT,
                'search_results',
            )
            os.makedirs(directory_path, exist_ok=True)
            # Имя файла с результатами поиска
            file_name = f"{get_unique_filename('advanced_search')}.xls"
            file_path = os.path.join(directory_path, file_name)

            # Сохранение файла
            workbook.save(file_path)

            # Возврат url сформированного файла с результатами поиска
            return os.path.join(
                settings.MEDIA_URL,
                'search_results',
                file_name
            )
    return False


@shared_task
def create_transactions_search_results_file(get_params, lang_code):
    """Возвращает url файла с результатами поиска по оповещениям."""
    form = get_search_form('transactions', get_params)
    # Валидация запроса
    if form.is_valid():
        s = get_search_in_transactions(form.cleaned_data)
        if s:
            # Сортировка
            if get_params.get('sort_by'):
                s = sort_results(s, get_params['sort_by'])
            else:
                s = s.sort('_score')

            if s.count() <= 5000:
                s = s.source(['search_data', 'Document'])

                # Сортировка
                if get_params.get('sort_by'):
                    s = sort_results(s, get_params['sort_by'])
                else:
                    s = s.sort('_score')

                # Данные для Excel-файла
                data = prepare_data_for_search_report(s, lang_code)

                # Формировние Excel-файла
                workbook = create_search_res_doc(data)

                directory_path = os.path.join(
                    settings.MEDIA_ROOT,
                    'search_results',
                )
                os.makedirs(directory_path, exist_ok=True)
                # Имя файла с результатами поиска
                file_name = f"{get_unique_filename('transactions_search')}.xls"
                file_path = os.path.join(directory_path, file_name)

                # Сохранение файла
                workbook.save(file_path)

                # Возврат url сформированного файла с результатами поиска
                return os.path.join(
                    settings.MEDIA_URL,
                    'search_results',
                    file_name
                )
    return False


@shared_task
def create_shared_docs_archive(id_app_number):
    """Возвращает url файла с архивом доступных всем документов."""
    try:
        app = IpcAppList.objects.get(id=id_app_number, registration_number__gt=0, obj_type_id__in=(1, 2, 3))
    except IpcAppList.DoesNotExist:
        return False

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
    return os.path.join(
        settings.MEDIA_URL,
        'shared_docs',
        file_name
    )