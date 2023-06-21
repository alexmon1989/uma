import datetime
from typing import List, Optional
import time
import copy
import os
from zipfile import ZipFile

from django.utils.translation import gettext as _
from django.conf import settings
from django.utils import translation

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from apps.search.models import IpcAppList, DeliveryDateCead, OrderService, OrderDocument
from apps.bulletin import services as bulletin_services
from apps.search.utils import filter_bad_apps, user_has_access_to_docs
from apps.search.dataclasses import InidCode, ApplicationDocument, ServiceExecuteResult, ServiceExecuteResultError

from uma.utils import get_user_or_anonymous


def application_get_stages_statuses(app_data: dict) -> Optional[List]:
    """Возвращает список со статусами этапов рассмотрения заявки."""
    obj_types_funcs = {
        1: application_get_inv_um_ld_stages_statuses,
        2: application_get_inv_um_ld_stages_statuses,
        3: application_get_inv_um_ld_stages_statuses,
        4: application_get_tm_stages_statuses,
        6: application_get_id_stages_statuses,
    }

    try:
        return obj_types_funcs[app_data['Document']['idObjType']](app_data)
    except KeyError:
        return None


def application_get_inv_um_ld_stages_statuses(app_data: dict) -> List:
    """Возвращает список со статусами этапов рассмотрения заявки на изобретение или полезную модель."""
    # Состояние делопроизводства
    is_stopped = False
    doc_types = [doc['DOCRECORD']['DOCTYPE'] for doc in app_data['DOCFLOW'].get('DOCUMENTS', [])
                 if doc['DOCRECORD'].get('DOCREGNUMBER')
                 or doc['DOCRECORD'].get('DOCBARCODE')
                 or doc['DOCRECORD'].get('DOCSENDINGDATE')]

    # Признаки того что делопроизводство остановлено
    for x in ['[В11]', '[В5]', '[В5а]', '[В5д]', '[В12]', '[В5б]', '[В16]', '[В10]']:
        for doc_type in doc_types:
            if x in doc_type:
                is_stopped = True

    # Признаки того что делопроизводство возобновлено
    if is_stopped:
        for x in ['[В21а]', '[В21б]', '[В21]', '[В22]']:
            for doc_type in doc_types:
                if x in doc_type:
                    is_stopped = False

    # Пройденные стадии
    done_stages = list()
    for stage in app_data['DOCFLOW'].get('STAGES', []):
        if stage['STAGERECORD']['STAGE'] == 'Встановлення дати подання національної заявки':
            for x in ['[В1]', '[В4]', '[В9]']:
                for doc_type in doc_types:
                    if x in doc_type:
                        done_stages.append(stage['STAGERECORD']['STAGE'])
                        break
        elif stage['STAGERECORD']['STAGE'] == 'Формальна експертиза заявок на винаходи і корисні моделі':
            for x in ['[В6]', '[В7]', '[В8]']:
                for doc_type in doc_types:
                    if x in doc_type:
                        done_stages.append(stage['STAGERECORD']['STAGE'])
                        break
        elif stage['STAGERECORD'].get('ENDDATE'):
            done_stages.append(stage['STAGERECORD']['STAGE'])

    # Коды сборов
    cl_codes = []
    for stage in app_data['DOCFLOW'].get('COLLECTIONS', []):
        if stage['CLRECORD'].get('CLCODE'):
            cl_codes.append(stage['CLRECORD']['CLCODE'])

    # Стадии делопроизводства по заявке
    stages = [
        {
            'title': _('Патент зареєстровано'),
            'status': 'done' if app_data['search_data']['obj_state'] == 2
                                or 'Підтримка чинності' in done_stages
            else 'not-active'
        },
        {
            'title': _('Підготовка до державної реєстрації та публікації'),
            'status': 'done' if app_data['search_data']['obj_state'] == 2
                                or 'Підготовка заявки до реєстрації патенту' in done_stages
            else 'not-active'
        },
        {
            'title': _('Очікування документа про сплату державного мита'),
            'status': 'done' if app_data['search_data']['obj_state'] == 2
                                or '19994' in cl_codes or '19996' in cl_codes
            else 'not-active'
        },
        {
            'title': _('Кваліфікаційна експертиза'),
            'status': 'done' if app_data['search_data']['obj_state'] == 2 or 'Кваліфікаційна експертиза' in done_stages
            else 'not-active'
        },
        {
            'title': _('Очікування клопотання про проведення кваліфікаційної експертизи'),
            'status': 'done' if app_data['search_data']['obj_state'] == 2
                                or 'Очікування клопотання та збору щодо КЕ' in done_stages
            else 'not-active'
        },
        {
            'title': _('Формальна експертиза'),
            'status': 'done' if app_data['search_data']['obj_state'] == 2
                                or 'Формальна експертиза заявок на винаходи і корисні моделі' in done_stages
            else 'not-active'
        },
        {
            'title': _('Встановлення дати подання'),
            'status': 'done' if app_data['search_data']['obj_state'] == 2
                                or 'Встановлення дати подання національної заявки' in done_stages
                                or 'Встановлення дати входження в національну фазу в Україні' in done_stages
            else 'not-active'
        },
        {
            'title': _('Реєстрація первинних документів, попередня експертиза та введення відомостей до бази даних'),
            'status': 'done'
        },
    ]

    # Неиспользуемые стадии при экспертизе заявок на полезные модели
    if app_data['Document']['idObjType'] == 2:
        stages[3]['status'] = 'not-used'
        stages[4]['status'] = 'not-used'

    # Определение текущей стадии или стадии, на которой было остановлено делопроизводство
    for i, s in enumerate(stages):
        if s['status'] == 'done':
            if i != 0:
                if is_stopped:
                    if i == 7:
                        # Поскольку стадия "Реєстрація первинних документів" всегда пройдена
                        stages[i - 1]['status'] = 'stopped'
                    else:
                        stages[i]['status'] = 'stopped'
                else:
                    stages[i - 1]['status'] = 'current'
            break

    return stages


def application_get_tm_stages_statuses(app_data: dict) -> List:
    """Возвращает список со статусами этапов рассмотрения заявки на ТМ."""
    if app_data['TradeMark'].get('TrademarkDetails', {}).get('stages'):  # Заявки из новой системы
        stages = list(map(lambda x: {'title': x['title'], 'status': x['status'].replace(';', '')},
                          app_data['TradeMark']['TrademarkDetails']['stages']))

        # Fix для свидетельств
        if app_data['search_data']['obj_state'] == 2:
            for stage in stages:
                stage['status'] = 'done'
            return stages

        # Fix
        prev_status = ''
        for stage in stages[::-1]:
            if stage["title"] == "Встановлення дати подання" \
                    and app_data['TradeMark'].get('TrademarkDetails', {}).get('Code_441'):
                if stage['status'] == 'current':
                    stages[3]['status'] = 'current'
                stage['status'] = 'done'
                continue

            if stage['status'] == 'current' == prev_status \
                    or (stage['status'] in ('done', 'current', 'stopped',)
                        and prev_status in ('current', 'not-active', 'stopped')):
                stage['status'] = 'not-active'

            prev_status = stage['status']

        return stages

    # "Старые" заявки

    mark_status_code = application_get_tm_fixed_mark_status_code(app_data)
    is_stopped = app_data['Document'].get('RegistrationStatus') == 'Діловодство за заявкою припинено' \
                 or mark_status_code == 8000

    if app_data['search_data']['obj_state'] == 2:
        stages_statuses = ['done' for _ in range(6)]
    else:
        stages_statuses = ['not-active' for _ in range(6)]

        for i, s in enumerate(stages_statuses):
            if mark_status_code >= (i + 2) * 1000:
                stages_statuses[i] = 'done'
            else:
                if is_stopped:
                    stages_statuses[i] = 'not-active'
                    if i > 1:
                        stages_statuses[i - 1] = 'stopped'
                    else:
                        stages_statuses[i] = 'stopped'
                else:
                    stages_statuses[i] = 'current'
                break

        if mark_status_code == 8000:
            stages_statuses[5] = 'stopped'

        # Если есть форма Т-08, то "Кваліфікаційна експертиза" пройдена
        if stages_statuses[2] == 'done' and stages_statuses[5] == 'not-active':
            for doc in app_data['TradeMark']['DocFlow']['Documents']:
                if 'Т-08' in doc['DocRecord'].get('DocFlow', {}).get('Documents', []):
                    stages_statuses[4] = 'current'
                    stages_statuses[3] = 'done'
                    break

        # Если есть форма Т-05, то "Формальна експертиза" пройдена (для случая если делопроизводство остановлено)
        if is_stopped:
            for doc in app_data['TradeMark'].get('DocFlow', {}).get('Documents', []):
                if 'Т-05' in doc['DocRecord'].get('DocType', ''):
                    stages_statuses[2] = 'done'
                    stages_statuses[3] = 'stopped'
                    break

    stages = [
        {
            'title': _('Торговельну марку зареєстровано'),
            'status': stages_statuses[5],
        },
        {
            'title': _('Підготовка до державної реєстрації та публікації'),
            'status': stages_statuses[4],
        },
        {
            'title': _('Кваліфікаційна експертиза'),
            'status': stages_statuses[3],
        },
        {
            'title': _('Формальна експертиза'),
            'status': stages_statuses[2],
        },
        {
            'title': _('Встановлення дати подання'),
            'status': stages_statuses[1],
        },
        {
            'title': _('Реєстрація первинних документів, попередня експертиза та введення відомостей до бази даних'),
            'status': stages_statuses[0],
        },
    ]

    return stages


def application_get_tm_fixed_mark_status_code(app_data):
    """Анализирует список документов ТМ и возвращает код статуса согласно их наличию."""
    result = int(app_data['Document'].get('MarkCurrentStatusCodeType', 0))
    for doc in app_data['TradeMark'].get('DocFlow', {}).get('Documents', []):
        if ('ТM-1.1' in doc['DocRecord']['DocType'] or 'ТМ-1.1' in doc['DocRecord']['DocType']) and result < 2000:
            result = 3000
        if ('Т-05' in doc['DocRecord']['DocType'] or 'Т-5' in doc['DocRecord']['DocType']) and result < 3000:
            result = 3000
        if 'Т-08' in doc['DocRecord']['DocType'] and result < 4000:
            result = 4000
    return result


def application_get_id_stages_statuses(app_data: dict) -> List:
    """Возвращает список со статусами этапов рассмотрения заявки на пром. образец."""
    if app_data['Design'].get('DesignDetails', {}).get('stages'):  # Заявки из новой системы
        stages = list(map(lambda x: {'title': x['title'], 'status': x['status'].replace(';', '')},
                          app_data['Design']['DesignDetails']['stages']))

        # Fix для патентов
        if app_data['search_data']['obj_state'] == 2:
            for stage in stages:
                stage['status'] = 'done'
            return stages

        # Fix
        prev_status = ''
        for stage in stages[::-1]:
            if stage['status'] == 'current' == prev_status or (
                    stage['status'] in ('done', 'current', 'stopped',) and prev_status in ('current', 'not-active')):
                stage['status'] = 'not-active'
            prev_status = stage['status']

        return stages

    design_status_code = int(app_data['Document'].get('DesignCurrentStatusCodeType', 0))
    is_stopped = app_data['Document'].get('RegistrationStatus') == 'Діловодство за заявкою припинено'

    if app_data['search_data']['obj_state'] == 2:
        stages_statuses = ['done' for _ in range(5)]
    else:
        stages_statuses = ['not-active' for _ in range(5)]
        marks = [2000, 4000, 5000, 5002, 6000]

        for i, s in enumerate(stages_statuses):
            if design_status_code >= marks[i]:
                stages_statuses[i] = 'done'
            else:
                if is_stopped:
                    stages_statuses[i] = 'not-active'
                    stages_statuses[i - 1] = 'stopped'
                else:
                    stages_statuses[i] = 'current'
                break

    stages = [
        {
            'title': _('Промисловий зразок зареєстровано'),
            'status': stages_statuses[4],
        },
        {
            'title': _('Підготовка до державної реєстрації та публікації'),
            'status': stages_statuses[3],
        },
        {
            'title': _('Експертиза заявки'),
            'status': stages_statuses[2],
        },
        {
            'title': _('Встановлення дати подання'),
            'status': stages_statuses[1],
        },
        {
            'title': _('Реєстрація первинних документів, попередня експертиза та введення відомостей до бази даних'),
            'status': stages_statuses[0],
        },
    ]

    return stages


def application_sort_transactions(app_data: dict) -> None:
    """Сортирует оповещения заявки."""
    # Изобретения, полезные модели, топографии
    if app_data['Document']['idObjType'] in (1, 2, 3):
        transactions = app_data['transactions']
        transactions.sort(
            key=lambda item: time.strptime(item.get('BULLETIN_DATE', '1970-01-01'), "%Y-%m-%d")
        )

    # Торговые марки
    elif app_data['Document']['idObjType'] == 4:
        try:
            transactions = app_data['TradeMark']['Transactions']['Transaction']
        except KeyError:
            pass
        else:
            transactions.sort(
                key=lambda item: time.strptime(item.get('@bulletinDate', '1970-01-01'), "%Y-%m-%d")
            )

    # Геогр. зазначення
    elif app_data['Document']['idObjType'] == 5:
        try:
            transactions = app_data['Geo']['Transactions']['Transaction']
        except KeyError:
            pass
        else:
            transactions.sort(
                key=lambda item: time.strptime(item.get('@bulletinDate', '1970-01-01'), "%Y-%m-%d")
            )

    # Пром. образцы
    elif app_data['Document']['idObjType'] == 6:
        try:
            transactions = app_data['Design']['Transactions']['Transaction']
        except KeyError:
            pass
        else:
            transactions.sort(
                key=lambda item: time.strptime(item.get('@bulletinDate', '1970-01-01'), "%Y-%m-%d")
            )


def application_73_contains_country_code(code: str, biblio_data: dict) -> bool:
    """Возвращает признак наличия определённого кода страны в поле 73."""
    code = code.lower()
    i_73_values = biblio_data.get('I_73')
    if i_73_values:
        for item in i_73_values:
            if item.get('I_73.C', '').lower() == code:
                return True
    return False


def application_filter_documents_im_um_ld(biblio_data: dict, documents_data: List[dict]) -> List[dict]:
    """Возвращает отфильтрованные документы изобретения, полезной модели, топографии."""
    # 73 код содержит ли код страны RU
    is_73_ru = application_73_contains_country_code('RU', biblio_data)

    res = []
    for doc in documents_data:
        doc_reg_number = doc['DOCRECORD'].get('DOCREGNUMBER', '')
        # Документы без номеров, дат
        if not doc_reg_number and not doc['DOCRECORD'].get('DOCSENDINGDATE'):
            continue

        # Внутренние документы
        if doc_reg_number.startswith('вн'):
            continue

        # Тип документа
        doc_type = doc['DOCRECORD'].get('DOCTYPE', '').lower()

        # В рез. список не включаются служебные записки и отчёты о поиске
        if 'службова' in doc_type or 'звіт про інформаційний пошук' in doc_type:
            continue

        # Если код владельца - RU, то не включать в рез. список документов документы В8, В9
        if ('[в8]' in doc_type or '[в9]' in doc_type) and is_73_ru:
            continue

        res.append(doc)

    return res


def application_filter_documents_tm_id(documents_data: List[dict]) -> List[dict]:
    """Возвращает отфильтрованные документы торг. марки, пром. образца."""
    res = []
    for doc in documents_data:
        doc_type = doc.get('DocRecord', {}).get('DocType', '').lower()
        doc_number = doc.get('DocRecord', {}).get('DocRegNumber', '').lower()

        # В рез. список не включаются служебные записки
        if 'службова' in doc_type or 'бібліографічні дані заявки на знак для товарів і послуг' in doc_type:
            continue
        # и внутренние документы
        if doc_number.startswith('вн'):
            continue

        res.append(doc)

    return res


def application_prepare_biblio_data_id(data: dict) -> dict:
    """Готовит библиографические данные пром. образца для отображения."""
    res = copy.deepcopy(data)
    # Нужно ли публиковать автора
    if 'DesignerDetails' in data and 'Designer' in data['DesignerDetails']:
        for i, designer in enumerate(res['DesignerDetails']['Designer']):
            # Значение поля Publicated - признак того надо ли публиковать автора
            if 'Publicated' in designer and not designer['Publicated']:
                del res['DesignerDetails']['Designer'][i]
    return res


def application_prepare_biblio_data_tm(data: dict, app_db_data: IpcAppList) -> dict:
    """Готовит библиографические данные ТМ для отображения."""
    res = copy.deepcopy(data)

    # Значение поля 441.
    # Если последнее изменение данных после значения settings.CODE_441_BUL_NUMBER_FROM_JSON_SINCE_DATE,
    # то необходимо отображать значение, которое вернулось с АС "Позначення",
    # а иначе брать номер бюллетеня из таблицы cl_list_official_bulletins_ip
    bulletin_date_until = datetime.datetime.strptime(settings.CODE_441_BUL_NUMBER_FROM_JSON_SINCE_DATE, '%d.%m.%Y')

    if 'Code_441_BulNumber' in res and 'Code_441' in res and app_db_data.lastupdate < bulletin_date_until:
        res['Code_441_BulNumber'] = bulletin_services.bulletin_get_number_441_code(res['Code_441'])

    return res


def application_get_app_db_data(app_id: int) -> IpcAppList:
    """Возвращает данные заявки, хранящиеся в БД."""
    return IpcAppList.objects.filter(pk=app_id).first()


def application_get_app_elasticsearch_data(app_id: int) -> dict:
    """Возвращает данные заявки, хранящиеся в ElasticSearch."""
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    q = Q(
        'bool',
        must=[Q('match', _id=app_id)],
    )
    # Фильтр заявок, которые не положено отображать
    q = filter_bad_apps(q)

    s = Search(index=settings.ELASTIC_INDEX_NAME).using(client).query(q).source(
        excludes=["*.DocBarCode", "*.DOCBARCODE"]
    ).execute()

    if not s:
        return {}
    return s[0].to_dict()


def inid_code_get_list(lang: str) -> List[InidCode]:
    """
    Возвращает список ИНИД-кодов объектов пром собств.

    TODO: Сделать выборку из БД
    TODO: Сделать кеширование
    """
    res = []

    if lang == 'ua':
        # ТМ регистрации
        inid_data = [
            InidCode(4, '540', 'Зображення знака', 2, True),
            InidCode(4, '141', 'Дата закінчення строку дії реєстрації знака', 2, True),
            InidCode(4, '111', 'Порядковий номер реєстрації', 2, True),
            InidCode(4, '151', 'Дата реєстрації', 2, True),
            InidCode(4, '181', 'Очікувана дата закінчення строку дії реєстрації', 2, True),
            InidCode(4, '186', 'Очікувана дата продовження строку дії реєстрації', 2, True),
            InidCode(4, '210', 'Номер заявки', 2, True),
            InidCode(4, '220', 'Дата подання заявки', 2, True),
            InidCode(4, '300', 'Дані щодо пріоритету відповідно до Паризької конвенції та інші дані, '
                               'пов\'язані зі старшинством або реєстрацією знака у країні походження', 2, True),
            InidCode(4, '441', 'Дата публікації відомостей про заявку та номер бюлетня', 2, True),
            InidCode(4, '450', 'Дата публікації відомостей про видачу свідоцтва', 2, True),
            InidCode(4, '531', 'Віденська класифікація', 2, True),
            InidCode(4, '731', 'Ім\'я та адреса заявника', 2, True),
            InidCode(4, '732', 'Ім\'я та адреса володільця реєстрації', 2, True),
            InidCode(4, '740', 'Ім\'я та адреса представника', 2, True),
            InidCode(4, '750', 'Адреса для листування', 2, True),
            InidCode(4, '591', 'Інформація щодо заявлених кольорів', 2, True),
            InidCode(4, '511', 'Індекси Ніццької класифікації', 2, True),
            InidCode(4, '526', 'Вилучення з охорони окремих елементів торговельної марки', 2, True),
        ]
        res.extend(inid_data)

        # ТМ заявки
        inid_data = [
            InidCode(4, '540', 'Зображення знака', 1, True),
            InidCode(4, '210', 'Номер заявки', 1, True),
            InidCode(4, '220', 'Дата подання заявки', 1, True),
            InidCode(4, '221', 'Дата надходження матеріалів заявки до НОІВ', 1, True),
            InidCode(4, '300', 'Дані щодо пріоритету відповідно до Паризької конвенції та інші дані, '
                               'пов\'язані зі старшинством або реєстрацією знака у країні походження', 1, True),
            InidCode(4, '441', 'Дата публікації відомостей про заявку та номер бюлетня', 1, True),
            InidCode(4, '531', 'Віденська класифікація', 1, True),
            InidCode(4, '731', 'Ім\'я та адреса заявника', 1, True),
            InidCode(4, '740', 'Ім\'я та адреса представника', 1, True),
            InidCode(4, '750', 'Адреса для листування', 1, True),
            InidCode(4, '591', 'Інформація щодо заявлених кольорів', 1, True),
            InidCode(4, '511', 'Індекси Ніццької класифікації', 1, True),
            InidCode(4, '526', 'Вилучення з охорони окремих елементів торговельної марки', 1, True),
        ]
        res.extend(inid_data)

        # Пром. образцы регистрации
        inid_data = [
            InidCode(6, '51', 'Індекс(и) Міжнародної класифікації промислових зразків (МКПЗ)', 2, True),
            InidCode(6, '11', 'Номер реєстрації (патенту)', 2, True),
            InidCode(6, '24', 'Дата, з якої є чинними права на промисловий зразок', 2, True),
            InidCode(6, '21', 'Номер заявки', 2, True),
            InidCode(6, '22', 'Дата подання заявки', 2, True),
            InidCode(6, '23', 'Дата виставкового пріоритету', 2, True),
            InidCode(6, '28', 'Кількість заявлених варіантів', 2, True),
            InidCode(6, '31', 'Номер попередньої заявки відповідно до Паризької конвенції', 2, True),
            InidCode(6, '32', 'Дата подання попередньої заявки відповідно до Паризької конвенції', 2, True),
            InidCode(6, '33', 'Двобуквений код держави-учасниці Паризької конвенції, до якої подано попередню заявку', 2, True),
            InidCode(6, '45', 'Дата публікації відомостей про видачу патенту та номер бюлетеня', 2, True),
            InidCode(6, '54', 'Назва промислового зразка', 2, True),
            InidCode(6, '55', 'Зображення промислового зразка та вказівка відносно кольорів', 2, True),
            InidCode(6, '71', "Ім'я (імена) та адреса (адреси) заявника (заявників)", 2, True),
            InidCode(6, '72', "Ім'я (імена) автора (авторів), якщо воно відоме", 2, True),
            InidCode(6, '73', "Ім’я або повне найменування власника(ів) патенту, його адреса та двобуквений код держави", 2, True),
            InidCode(6, '74', "Ім'я (імена) та адреса (адреси) представника (представників)", 2, True),
            InidCode(6, '98', "Адреса для листування", 2, True),
        ]
        res.extend(inid_data)

        # Пром. образцы заявки
        inid_data = [
            InidCode(6, '51', 'Індекс(и) Міжнародної класифікації промислових зразків (МКПЗ)', 1, True),
            InidCode(6, '21', 'Номер заявки', 1, True),
            InidCode(6, '22', 'Дата подання заявки', 1, True),
            InidCode(6, '23', 'Дата виставкового пріоритету', 1, True),
            InidCode(6, '28', 'Кількість заявлених варіантів', 1, True),
            InidCode(6, '31', 'Номер попередньої заявки відповідно до Паризької конвенції', 1, True),
            InidCode(6, '32', 'Дата подання попередньої заявки відповідно до Паризької конвенції', 1, True),
            InidCode(6, '33', 'Двобуквений код держави-учасниці Паризької конвенції, до якої подано попередню заявку',
                     1, True),
            InidCode(6, '54', 'Назва промислового зразка', 1, True),
            InidCode(6, '55', 'Зображення промислового зразка та вказівка відносно кольорів', 1, True),
            InidCode(6, '71', "Ім'я (імена) та адреса (адреси) заявника (заявників)", 1, True),
            InidCode(6, '72', "Ім'я (імена) автора (авторів), якщо воно відоме", 1, True),
            InidCode(6, '74', "Ім'я (імена) та адреса (адреси) представника (представників)", 1, True),
            InidCode(6, '98', "Адреса для листування", 1, True),
        ]
        res.extend(inid_data)

        # Мадрид
        for obj_type_id in [9, 14]:
            inid_data = [
                InidCode(obj_type_id, '111', 'Номер міжнародної реєстрації', 2, True),
                InidCode(obj_type_id, '151', 'Дата міжнародної реєстрації', 2, True),
                InidCode(obj_type_id, '180', 'Очікувана дата закінчення строку дії реєстрації/продовження', 2, True),
                InidCode(obj_type_id, '441', 'Дата публікації відомостей про міжнародну реєстрацію торговельної марки, що надійшла для проведення експертизи', 2, True),
                InidCode(obj_type_id, '450', 'Дата публікації відомостей про міжнародну реєстрацію та номер бюлетеню Міжнародного бюро ВОІВ', 2, True),
                InidCode(obj_type_id, '732', 'Ім\'я та адреса володільця реєстрації', 2, True),
                InidCode(obj_type_id, '740', 'Ім\'я та адреса представника', 2, True),
                InidCode(obj_type_id, '821', 'Базова заявка', 2, True),
                InidCode(obj_type_id, '891', 'Дата територіального поширення міжнародної реєстрації', 2, True),
                InidCode(obj_type_id, '540', 'Зображення торговельної марки', 2, True),
                InidCode(obj_type_id, '511', 'Індекс (індекси) МКТП та перелік товарів і послуг', 2, True),
            ]
            res.extend(inid_data)

        # Изобретения, полезные модели (регистрации)
        for obj_type_id in [1, 2]:
            inid_data = [
                InidCode(obj_type_id, '11', 'Номер патенту', 2, True),
                InidCode(obj_type_id, '21', 'Номер заявки', 2, True),
                InidCode(obj_type_id, '22', 'Дата подання заявки', 2, True),
                InidCode(obj_type_id, '24', 'Дата, з якої є чинними права', 2, True),
                InidCode(obj_type_id, '31', 'Номер попередньої заявки', 2, True),
                InidCode(obj_type_id, '32', 'Дата подання попередньої заявки', 2, True),
                InidCode(obj_type_id, '33', 'Двобуквений код держави', 2, True),
                InidCode(obj_type_id, '41', 'Дата публікації заявки', 2, True),
                InidCode(obj_type_id, '46', 'Дата публікації відомостей про видачу патенту, номер бюлетня', 2, True),
                InidCode(obj_type_id, '51', 'Iндекс МПК', 2, True),
                InidCode(obj_type_id, '54', 'Назва винаходу (корисної моделі)', 2, True),
                InidCode(obj_type_id, '56', 'Аналоги винаходу', 2, True),
                InidCode(obj_type_id, '62', 'Номер та дата більш ранньої заявки, з якої було виділено даний патентний документ', 2, True),
                InidCode(obj_type_id, '71', 'Заявник', 2, True),
                InidCode(obj_type_id, '72', 'Винахідник', 2, True),
                InidCode(obj_type_id, '73', 'Власник', 2, True),
                InidCode(obj_type_id, '74', 'Представник', 2, True),
                InidCode(obj_type_id, '85', 'Дата входження до національної фази', 2, True),
                InidCode(obj_type_id, '86', 'Номер та дата подання заявки РСТ', 2, True),
                InidCode(obj_type_id, '98', 'Адреса для листування', 2, True),
            ]
            res.extend(inid_data)

        # Изобретения, полезные модели (заявки)
        for obj_type_id in [1, 2]:
            inid_data = [
                InidCode(obj_type_id, '21', 'Номер заявки', 1, True),
                InidCode(obj_type_id, '22', 'Дата подання заявки', 1, True),
                InidCode(obj_type_id, '31', 'Номер попередньої заявки', 1, True),
                InidCode(obj_type_id, '32', 'Дата подання попередньої заявки', 1, True),
                InidCode(obj_type_id, '33', 'Двобуквений код держави', 1, True),
                InidCode(obj_type_id, '41', 'Дата публікації заявки', 1, True),
                InidCode(obj_type_id, '51', 'Iндекс МПК', 1, True),
                InidCode(obj_type_id, '54', 'Назва винаходу (корисної моделі)', 1, True),
                InidCode(obj_type_id, '56', 'Аналоги винаходу', 1, True),
                InidCode(obj_type_id, '71', 'Заявник', 1, True),
                InidCode(obj_type_id, '72', 'Винахідник', 1, True),
                InidCode(obj_type_id, '74', 'Представник', 1, True),
                InidCode(obj_type_id, '85', 'Дата входження до національної фази', 1, True),
                InidCode(obj_type_id, '86', 'Номер та дата подання заявки РСТ', 1, True),
                InidCode(obj_type_id, '98', 'Адреса для листування', 1, True),
            ]
            res.extend(inid_data)

        # Топографии (регистрации)
        inid_data = [
            InidCode(3, '11', 'Номер свідоцтва', 2, True),
            InidCode(3, '21', 'Номер заявки', 2, True),
            InidCode(3, '22', 'Дата подання заявки', 2, True),
            InidCode(3, '24', 'Дата, з якої є чинними права', 2, True),
            InidCode(3, '31', 'Номер попередньої заявки', 2, True),
            InidCode(3, '32', 'Дата подання попередньої заявки', 2, True),
            InidCode(3, '33', 'Двобуквений код держави', 2, True),
            InidCode(3, '41', 'Дата публікації заявки', 2, True),
            InidCode(3, '46', 'Дата публікації відомостей про видачу патенту, номер бюлетня', 2,
                     True),
            InidCode(3, '54', 'Назва інтегральної мікросхеми', 2, True),
            InidCode(3, '71', 'Заявник', 2, True),
            InidCode(3, '72', 'Винахідник', 2, True),
            InidCode(3, '73', 'Власник', 2, True),
            InidCode(3, '74', 'Представник', 2, True),
            InidCode(3, '98', 'Адреса для листування', 2, True),
        ]
        res.extend(inid_data)

        # Географічні зазначення (заявки)
        inid_data = [
            InidCode(5, '190', 'Держава реєстрації КЗПТ', 1, True),
            InidCode(5, '210', 'Номер заявки', 1, True),
            InidCode(5, '220', 'Дата подання заявки', 1, True),
            InidCode(5,
                     '441',
                     'Дата публікації відомостей про заявку (заявлене географічне зазначення) та номер бюлетеня',
                     1,
                     True),
            InidCode(5, '539.I', 'Географічне зазначення', 1, True),
            InidCode(5, '540', 'Назва товару', 1, True),
            InidCode(5, '4551', 'Кваліфікація географічного зазначення', 1, True),
            InidCode(5, '529.A', 'Опис меж географічного місця', 1, True),
            InidCode(5, '539.D', 'Опис товару, для якого географічне зазначення заявляється на реєстрацію', 1, True),
            InidCode(5, '4573',
                     'Опис взаємозв’язку товару з географічним середовищем чи географічним місцем походженням',
                     1, True),
            InidCode(5, '731', 'Відомості про заявника', 1, True),
            InidCode(5, '9441', 'Специфікація товару', 1, True),
        ]
        res.extend(inid_data)

        # Географічні зазначення (регистрации)
        inid_data = [
            InidCode(5, '111', 'Номер реєстрації', 2, True),
            InidCode(5, '151', 'Дата реєстрації', 2, True),
            InidCode(5, '190', 'Держава реєстрації КЗПТ', 2, True),
            InidCode(5, '210', 'Номер заявки', 2, True),
            InidCode(5, '220', 'Дата подання заявки', 2, True),
            InidCode(5,
                     '441',
                     'Дата публікації відомостей про заявку (заявлене географічне зазначення) та номер бюлетеня',
                     2,
                     True),
            InidCode(5, '539.I', 'Географічне зазначення', 2, True),
            InidCode(5, '540', 'Назва товару', 2, True),
            InidCode(5, '4551', 'Кваліфікація географічного зазначення', 2, True),
            InidCode(5, '529.A', 'Опис меж географічного місця', 2, True),
            InidCode(5, '539.D', 'Опис товару, для якого географічне зазначення заявляється на реєстрацію', 2, True),
            InidCode(5, '4573',
                     'Опис взаємозв’язку товару з географічним середовищем чи географічним місцем походженням',
                     2, True),
            InidCode(5, '731', 'Відомості про заявника', 2, True),
            InidCode(5, '9441', 'Специфікація товару', 2, True),
        ]
        res.extend(inid_data)

        # Авт. право (регистрации)
        for obj_type_id in [10, 13]:
            inid_data = [
                InidCode(obj_type_id, '11', 'Номер свідоцтва про реєстрацію авторського права на твір', 2, True),
                InidCode(obj_type_id, '15', 'Дата реєстрації авторського права', 2, True),
                InidCode(obj_type_id, '29', 'Об\'єкт авторського права, до якого належить твір', 2, True),
                InidCode(obj_type_id, '45.D', 'Дата публікації', 2, True),
                InidCode(obj_type_id, '45.N', 'Номер бюлетеня', 2, True),
                InidCode(obj_type_id, '54', 'Вид, повна та скорочена назва твору (творів)', 2, True),
                InidCode(obj_type_id, '57', 'Анотація', 2, True),
                InidCode(obj_type_id, '72', 'Повне ім\'я та/або псевдонім автора (авторів), чи позначення «Анонімно»', 2, True),
                InidCode(obj_type_id, '58', 'Вихідні дані для оприлюднених творів', 2, True),
                InidCode(obj_type_id, '77', 'Повне ім\'я або повне офіційне найменування роботодавця', 2, True),
            ]
            res.extend(inid_data)

        # Договора авт. право (регистрации)
        for obj_type_id in [11, 12]:
            inid_data = [
                InidCode(obj_type_id, '11', 'Номер реєстрації договору', 2, True),
                InidCode(obj_type_id, '15', 'Дата реєстрації договору', 2, True),
                InidCode(obj_type_id, '27', 'Вид договору', 2, True),
                InidCode(obj_type_id, '29', 'Об\'єкт авторського права, до якого належить твір', 2, True),
                InidCode(obj_type_id, '54', 'Вид, повна та скорочена назва твору (творів)', 2, True),
                InidCode(obj_type_id, '72', 'Повне ім\'я та/або псевдонім автора (авторів) твору', 2, True),
                InidCode(obj_type_id, '75', 'Повне ім\'я фізичної(их) або повне офіційне найменування юридичної(их) '
                                            'особи (осіб), сторін договору', 2, True),
            ]
            res.extend(inid_data)

    elif lang == 'en':
        # ТМ регистрации
        inid_data = [
            InidCode(4, '540', 'Reproduction of the mark', 2, True),
            InidCode(4, '141', 'Date of the termination of the registration of the mark', 2, True),
            InidCode(4, '111', 'Serial number of the registration', 2, True),
            InidCode(4, '151', 'Date of the registration', 2, True),
            InidCode(4, '181', 'Expected expiration date of the registration', 2, True),
            InidCode(4, '186', 'Expected prolongation date of the registration', 2, True),
            InidCode(4, '210', 'Serial number of the application', 2, True),
            InidCode(4, '220', 'Date of filing of the application', 2, True),
            InidCode(4, '300', 'Priority data according to the Paris Convention and other data related to seniority '
                               'or registration of the mark in the origin country', 2, True),
            InidCode(4, '441', 'Application publication date and bulletin number', 2, True),
            InidCode(4, '450', 'Date of publication of information on the issuance of the certificate', 2, True),
            InidCode(4, '531', 'Vienna Classification', 2, True),
            InidCode(4, '731', 'Name and address of the applicant', 2, True),
            InidCode(4, '732', 'Name and address of the holder of the registration', 2, True),
            InidCode(4, '740', 'Name and address of the representative', 1, True),
            InidCode(4, '750', 'Address for correspondence', 1, True),
            InidCode(4, '591', 'Information concerning colors claimed', 2, True),
            InidCode(4, '511', 'Nice Classification indexes', 2, True),
            InidCode(4, '526', 'Withdrawal from protection of certain elements of the trademark', 2, True),
        ]
        res.extend(inid_data)

        # ТМ заявки
        inid_data = [
            InidCode(4, '540', 'Reproduction of the mark', 1, True),
            InidCode(4, '210', 'Serial number of the application', 1, True),
            InidCode(4, '220', 'Date of filing of the application', 1, True),
            InidCode(4, '221', 'Date of receipt of application materials to NIPIO', 1, True),
            InidCode(4, '300', 'Priority data according to the Paris Convention and other data related to seniority '
                               'or registration of the mark in the origin country', 1, True),
            InidCode(4, '441', 'Application publication date and bulletin number', 1, True),
            InidCode(4, '531', 'Vienna Classification', 1, True),
            InidCode(4, '731', 'Name and address of the applicant', 1, True),
            InidCode(4, '740', 'Name and address of the representative', 1, True),
            InidCode(4, '750', 'Address for correspondence', 1, True),
            InidCode(4, '591', 'Information concerning colors claimed', 1, True),
            InidCode(4, '511', 'Nice Classification indexes', 1, True),
            InidCode(4, '526', 'Withdrawal from protection of certain elements of the trademark', 1, True),
        ]
        res.extend(inid_data)

        # Пром. образцы регистрации
        inid_data = [
            InidCode(6, '51', 'International Classification for Industrial Designs', 2, True),
            InidCode(6, '11', 'Serial number of the registration', 2, True),
            InidCode(6, '24', 'Date from which the industrial design right has effect', 2, True),
            InidCode(6, '21', 'Serial number of the application', 2, True),
            InidCode(6, '22', 'Date of filing of the application', 2, True),
            InidCode(6, '23', 'Name and place of exhibition, and date on which the industrial design was first exhibited there (exhibition priority data)', 2, True),
            InidCode(6, '28', 'Number of industrial designs included in the application', 2, True),
            InidCode(6, '31', 'Serial number assigned to the priority application', 2, True),
            InidCode(6, '32', 'Date of filing of the priority application', 2, True),
            InidCode(6, '33', 'Two-letter code, according to WIPO Standard ST.3, identifying the authority with which the priority application was made',
                     2, True),
            InidCode(6, '45', 'Date of publication of information on patent issuance and bulletin number', 2, True),
            InidCode(6, '54', 'Designation of article(s) or product(s) covered by the industrial design or title of the industrial design', 2, True),
            InidCode(6, '55', 'Images', 2, True),
            InidCode(6, '71', "Name(s) and address(es) of the applicant(s)", 2, True),
            InidCode(6, '72', "Name(s) of the creator(s) if known to be such", 2, True),
            InidCode(6, '73', "Name(s) and address(es) of the owner(s)", 2, True),
            InidCode(6, '74', "Name(s) and address(es) of the representative(s)", 2, True),
            InidCode(6, '98', "Correspondense address", 2, True),
        ]
        res.extend(inid_data)

        # Пром. образцы заявки
        inid_data = [
            InidCode(6, '51', 'International Classification for Industrial Designs', 1, True),
            InidCode(6, '21', 'Serial number of the application', 1, True),
            InidCode(6, '22', 'Date of filing of the application', 1, True),
            InidCode(6, '23',
                     'Name and place of exhibition, and date on which the industrial design was first exhibited there (exhibition priority data)',
                     1, True),
            InidCode(6, '28', 'Number of industrial designs included in the application', 1, True),
            InidCode(6, '31', 'Serial number assigned to the priority application', 1, True),
            InidCode(6, '32', 'Date of filing of the priority application', 1, True),
            InidCode(6, '33',
                     'Two-letter code, according to WIPO Standard ST.3, identifying the authority with which the priority application was made',
                     1, True),
            InidCode(6, '54',
                     'Designation of article(s) or product(s) covered by the industrial design or title of the industrial design',
                     1, True),
            InidCode(6, '55', 'Images', 1, True),
            InidCode(6, '71', "Name(s) and address(es) of the applicant(s)", 1, True),
            InidCode(6, '72', "Name(s) of the creator(s) if known to be such", 1, True),
            InidCode(6, '74', "Name(s) and address(es) of the representative(s)", 1, True),
            InidCode(6, '98', "Correspondense address", 1, True),
        ]
        res.extend(inid_data)

        # Мадрид
        for obj_type_id in [9, 14]:
            inid_data = [
                InidCode(obj_type_id, '111', 'International registration number', 2, True),
                InidCode(obj_type_id, '151', 'Date of international registration', 2, True),
                InidCode(obj_type_id, '180', 'Expected expiration date of the registration', 2, True),
                InidCode(obj_type_id, '441', 'Application publication date and bulletin number', 2, True),
                InidCode(obj_type_id, '450', 'Date of publication of information on international registration and number of the WIPO International Bureau bulletin', 2, True),
                InidCode(obj_type_id, '732', 'Name and address of the holder of the registration', 2, True),
                InidCode(obj_type_id, '740', 'Name and address of the representative', 2, True),
                InidCode(obj_type_id, '821', 'Base application', 2, True),
                InidCode(obj_type_id, '891', 'Date of territorial distribution of international registration', 2, True),
                InidCode(obj_type_id, '540', 'Brand image', 2, True),
                InidCode(obj_type_id, '511', 'ICCI index (s) and list of goods and services', 2, True),
            ]
            res.extend(inid_data)

        # Изобретения, полезные модели (регистрации)
        for obj_type_id in [1, 2]:
            inid_data = [
                InidCode(obj_type_id, '11', 'Number of the patent, SPC or patent document', 2, True),
                InidCode(obj_type_id, '21', 'Number assigned to the application', 2, True),
                InidCode(obj_type_id, '22', 'Date of filing of the application', 2, True),
                InidCode(obj_type_id, '24', 'Date from which industrial property rights may have effec', 2, True),
                InidCode(obj_type_id, '31', 'Number assigned to priority application', 2, True),
                InidCode(obj_type_id, '32', 'Date of filing of priority application', 2, True),
                InidCode(obj_type_id, '33', 'Twoleter of country code', 2, True),
                InidCode(obj_type_id, '41', 'Date of publication of application', 2, True),
                InidCode(obj_type_id, '46', 'Bulletin number and date of publication about patents grant', 2,
                         True),
                InidCode(obj_type_id, '51', 'Internmational patent classification', 2, True),
                InidCode(obj_type_id, '54', 'Title of the invention', 2, True),
                InidCode(obj_type_id, '56', 'Prior art documents, if separate from descriptive text', 2, True),
                InidCode(obj_type_id, '62',
                         'Number and date of the earlier application from which the present patent document has been divided up', 2,
                         True),
                InidCode(obj_type_id, '71', 'Applicant', 2, True),
                InidCode(obj_type_id, '72', 'Inventor', 2, True),
                InidCode(obj_type_id, '73', 'Name of grantee, holder, assignee or owner', 2, True),
                InidCode(obj_type_id, '74', 'Name of attorney or agent', 2, True),
                InidCode(obj_type_id, '85', 'Date of publication about patents grant', 2, True),
                InidCode(obj_type_id, '86', 'Number and date of filing of PCT Application', 2, True),
                InidCode(obj_type_id, '98', 'Mailing address', 2, True),
            ]
            res.extend(inid_data)

        # Изобретения, полезные модели (заявки)
        for obj_type_id in [1, 2]:
            inid_data = [
                InidCode(obj_type_id, '21', 'Number assigned to the application', 1, True),
                InidCode(obj_type_id, '22', 'Date of filing of the application', 1, True),
                InidCode(obj_type_id, '31', 'Number assigned to priority application', 1, True),
                InidCode(obj_type_id, '32', 'Date of filing of priority application', 1, True),
                InidCode(obj_type_id, '33', 'Twoleter of country code', 1, True),
                InidCode(obj_type_id, '41', 'Date of publication of application', 1, True),
                InidCode(obj_type_id, '51', 'Internmational patent classification', 1, True),
                InidCode(obj_type_id, '54', 'Title of the invention', 1, True),
                InidCode(obj_type_id, '56', 'Prior art documents, if separate from descriptive text', 1, True),
                InidCode(obj_type_id, '71', 'Applicant', 1, True),
                InidCode(obj_type_id, '72', 'Inventor', 1, True),
                InidCode(obj_type_id, '74', 'Name of attorney or agent', 1, True),
                InidCode(obj_type_id, '85', 'Date of publication about patents grant', 1, True),
                InidCode(obj_type_id, '86', 'Number and date of filing of PCT Application', 1, True),
                InidCode(obj_type_id, '98', 'Mailing address', 1, True),
            ]
            res.extend(inid_data)

        # Топографии (регистрации)
        inid_data = [
            InidCode(3, '11', 'Number of the patent, SPC or patent document', 2, True),
            InidCode(3, '21', 'Number assigned to the application', 2, True),
            InidCode(3, '22', 'Date of filing of the application', 2, True),
            InidCode(3, '24', 'Date from which industrial property rights may have effect', 2, True),
            InidCode(3, '31', 'Number assigned to priority application', 2, True),
            InidCode(3, '32', 'Date of filing of priority application', 2, True),
            InidCode(3, '33', 'Twoleter of country code', 2, True),
            InidCode(3, '41', 'Date of publication of application', 2, True),
            InidCode(3, '46', 'Bulletin number and date of publication about patents grant', 2,
                     True),
            InidCode(3, '54', 'Title of Integral micro ciquit', 2, True),
            InidCode(3, '71', 'Applicant', 2, True),
            InidCode(3, '72', 'Inventor', 2, True),
            InidCode(3, '73', 'Name of grantee, holder, assignee or owner', 2, True),
            InidCode(3, '74', 'Name of attorney or agent', 2, True),
            InidCode(3, '98', 'Mailing address', 2, True),
        ]
        res.extend(inid_data)

        # Географічні зазначення (заявки)
        inid_data = [
            InidCode(5, '190', 'State of registration of the qualified indication of origin of the product', 1, True),
            InidCode(5, '210', 'Application number', 1, True),
            InidCode(5, '220', 'Date of filing of the application', 1, True),
            InidCode(5,
                     '441',
                     'Application publication date, bulletin number',
                     1,
                     True),
            InidCode(5, '539.I', 'Geographical indication', 1, True),
            InidCode(5, '540', 'Name of the product', 1, True),
            InidCode(5, '4551', 'Кваліфікація географічного зазначення', 1, True),
            InidCode(5, '529.A', 'Description of the boundaries of a geographical place', 1, True),
            InidCode(5, '539.D', 'Description of the product for which the geographical indication is applied for registration', 1, True),
            InidCode(5, '4573',
                     'Description of the product\'s relationship with the geographic environment or geographic place of origin',
                     1, True),
            InidCode(5, '731', 'Information about applicant', 1, True),
            InidCode(5, '9441', 'Specification', 1, True),
        ]
        res.extend(inid_data)

        # Географічні зазначення (регистрации)
        inid_data = [
            InidCode(5, '111', 'Registration number', 2, True),
            InidCode(5, '151', 'Date of the registration', 2, True),
            InidCode(5, '190', 'State of registration of the qualified indication of origin of the product', 2, True),
            InidCode(5, '210', 'Application number', 2, True),
            InidCode(5, '220', 'Date of filing of the application', 2, True),
            InidCode(5,
                     '441',
                     'Application publication date, bulletin number',
                     1,
                     True),
            InidCode(5, '539.I', 'Geographical indication', 2, True),
            InidCode(5, '540', 'Name of the product', 2, True),
            InidCode(5, '4551', 'Qualification of geographical indication', 2, True),
            InidCode(5, '529.A', 'Description of the boundaries of a geographical place', 2, True),
            InidCode(5, '539.D', 'Description of the product for which the geographical indication '
                                 'is applied for registration', 2, True),
            InidCode(5, '4573',
                     'Description of the product\'s relationship with the geographic environment '
                     'or geographic place of origin',
                     2, True),
            InidCode(5, '731', 'Information about applicant', 2, True),
            InidCode(5, '9441', 'Specification', 2, True),
        ]
        res.extend(inid_data)

        # Авт. право (регистрации)
        for obj_type_id in [10, 13]:
            inid_data = [
                InidCode(obj_type_id, '11', 'The number of the copyright registration certificate for the office work',
                         2, True),
                InidCode(obj_type_id, '15', 'Copyright registration date', 2, True),
                InidCode(obj_type_id, '29', 'The object of copyright to which the work related', 2, True),
                InidCode(obj_type_id, '45.D', 'Date of publication', 2, True),
                InidCode(obj_type_id, '45.N', 'Bulletin number', 2, True),
                InidCode(obj_type_id, '54', 'Type, full and abbreviated title of the work (works)', 2, True),
                InidCode(obj_type_id, '57', 'Annotation', 2, True),
                InidCode(obj_type_id, '72', 'Name(s) of the creator(s) if known to be such', 2, True),
                InidCode(obj_type_id, '58', 'Initial data for published works', 2, True),
                InidCode(obj_type_id, '77', 'Name(s) and address(es) of the Employer(s)', 2, True),
            ]
            res.extend(inid_data)

        # Договора авт. право (регистрации)
        for obj_type_id in [11, 12]:
            inid_data = [
                InidCode(obj_type_id, '11', 'Agreement registration number', 2, True),
                InidCode(obj_type_id, '15', 'Agreement registration date', 2, True),
                InidCode(obj_type_id, '27', 'Kind of agreement', 2, True),
                InidCode(obj_type_id, '29', 'The object of copyright to which the work related', 2, True),
                InidCode(obj_type_id, '54', 'Type, full and abbreviated title of the work (works)', 2, True),
                InidCode(obj_type_id, '72', 'Name(s) of the creator(s)', 2, True),
                InidCode(obj_type_id, '75', 'Name of the natural person(s) or full official name of the legal '
                                            'entity(ies), parties to the agreement', 2, True),
            ]
            res.extend(inid_data)
    return res


def document_get_receive_date_cead(id_doc_cead: int) -> datetime.datetime | None:
    """Получает (из ЦЕАД) дату получения документа заявителем."""
    item = DeliveryDateCead.objects.using('e_archive').filter(id_doc_cead=id_doc_cead).first()
    if item:
        return item.receive_date
    return None


class DownloadDocumentsService:
    """Сервис, который скачивает документы из EArchive для пользователя."""
    cead_ids: List[int]  # список идентификаторов документов ЦЕАД для скачивания
    application_id: int  # идентификатор заявки (поле idAPPNumber из таблицы IPC_APPList базы данных UMA)
    application_data: dict
    user_id: int  # идентификатор пользователя
    user_ip_address: str  # ip адрес пользователя
    documents: List[ApplicationDocument] = []  # Список всех документов заявки
    documents_wo_receive_date: List[ApplicationDocument] = []  # Список документов без даты получения
    es_client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    order: OrderService

    # Типы документов для проверки есть ли у них дата доставки
    _doc_types_to_check = ['Т-8', 'Т-19', 'П-8', 'П-19', 'Т8', 'Т19', 'П8', 'П19']

    def _set_application(self) -> None:
        """Получает данные заявки из ElasticSearch."""
        q = Q(
            'bool',
            must=[Q('match', _id=self.application_id)],
        )
        s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.es_client).query(q).execute()
        if not s:
            self.application_data = {}
        else:
            self.application_data = s[0].to_dict()

    def _set_application_documents(self) -> None:
        """Устанавливает список всех документов заявки."""
        documents = []
        if self.application_data['Document']['idObjType'] in (1, 2, 3):
            for doc in self.application_data['DOCFLOW']['DOCUMENTS']:
                if doc['DOCRECORD'].get('DOCIDDOCCEAD'):
                    documents.append(
                        ApplicationDocument(
                            title=doc['DOCRECORD'].get('DOCTYPE'),
                            reg_number=doc['DOCRECORD'].get('DOCREGNUMBER'),
                            id_doc_cead=doc['DOCRECORD'].get('DOCIDDOCCEAD'),
                        )
                    )

            # Если это охранный документ, то нужно ещё добавить в список документы заявки
            if self.application_data['search_data']['obj_state'] == 2:
                q = Q(
                    'query_string',
                    query=f"search_data.obj_state:1 AND search_data.app_number:{self.application_data['search_data']['app_number']}",
                )
                s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.es_client).query(q).execute()
                if s:
                    app_hit = s[0].to_dict()
                    for doc in app_hit.get('DOCFLOW', {}).get('DOCUMENTS', []):
                        if doc['DOCRECORD'].get('DOCIDDOCCEAD'):
                            documents.append(
                                ApplicationDocument(
                                    title=doc['DOCRECORD'].get('DOCTYPE'),
                                    reg_number=doc['DOCRECORD'].get('DOCREGNUMBER'),
                                    id_doc_cead=doc['DOCRECORD'].get('DOCIDDOCCEAD'),
                                )
                            )

        elif self.application_data['Document']['idObjType'] == 4:
            for doc in self.application_data['TradeMark']['DocFlow']['Documents']:
                if doc['DocRecord'].get('DocIdDocCEAD'):
                    documents.append(
                        ApplicationDocument(
                            title=doc['DocRecord'].get('DocType'),
                            reg_number=doc['DocRecord'].get('DocRegNumber'),
                            id_doc_cead=doc['DocRecord'].get('DocIdDocCEAD'),
                        )
                    )

        elif self.application_data['Document']['idObjType'] == 5:
            for doc in self.application_data['Geo']['DocFlow']['Documents']:
                if doc['DocRecord'].get('DocIdDocCEAD'):
                    documents.append(
                        ApplicationDocument(
                            title=doc['DocRecord'].get('DocType'),
                            reg_number=doc['DocRecord'].get('DocRegNumber'),
                            id_doc_cead=doc['DocRecord'].get('DocIdDocCEAD'),
                        )
                    )

        elif self.application_data['Document']['idObjType'] == 6:
            for doc in self.application_data['Design']['DocFlow']['Documents']:
                if doc['DocRecord'].get('DocIdDocCEAD'):
                    documents.append(
                        ApplicationDocument(
                            title=doc['DocRecord'].get('DocType'),
                            reg_number=doc['DocRecord'].get('DocRegNumber'),
                            id_doc_cead=doc['DocRecord'].get('DocIdDocCEAD'),
                        )
                    )

        self.documents = documents

    def _check_correct_cead_ids(self) -> bool:
        """Проверяет, все ли документы для скачивания принадлежат заявке."""
        application_documents_cead_ids = [int(x.id_doc_cead) for x in self.documents]
        for id_doc_cead in self.cead_ids:
            if int(id_doc_cead) not in application_documents_cead_ids:
                return False
        return True

    def _set_docs_wo_receive_date(self) -> None:
        """Проверяет, все ли документы для скачивания имеют дату получения.
        Проверяются документы типов 'Т-8', 'Т-19', 'П-8', 'П-19'"""
        self.documents_wo_receive_date = []
        for id_doc_cead in self.cead_ids:
            for doc in self.documents:
                if int(doc.id_doc_cead) == int(id_doc_cead) \
                        and any([x in doc.title for x in self._doc_types_to_check]):
                    receive_date = document_get_receive_date_cead(id_doc_cead)
                    if not receive_date:
                        self.documents_wo_receive_date.append(doc)

    def _create_order(self) -> None:
        """Создаёт заказ на получение документов для внешнего сервиса Стол Заказов."""
        self.order = OrderService(
            user_id=self.user_id,
            ip_user=self.user_ip_address,
            app_id=self.application_id
        )
        self.order.save()
        for cead_id in self.cead_ids:
            OrderDocument.objects.create(order=self.order, id_cead_doc=cead_id)

    def _wait_order_completed(self, attempts=10, timeout=2) -> bool:
        """Ждёт выполнения заказа внешним сервисом Стол Заказов."""
        completed = False
        counter = 0
        while completed is False:
            self.order.refresh_from_db()
            if self.order.order_completed:
                return True
            else:
                if counter == attempts:
                    return False
                counter += 1
                time.sleep(timeout)

    def _create_zip(self) -> str:
        """Создаёт архив с документами отработанного заказа."""
        file_zip_name = f"docs_{self.order.id}.zip"
        file_path_zip = os.path.join(
            settings.ORDERS_ROOT,
            str(self.order.user_id),
            str(self.order.id),
            file_zip_name
        )
        with ZipFile(file_path_zip, 'w') as zip_:
            for document in self.order.orderdocument_set.all():
                zip_.write(
                    os.path.join(
                        settings.DOCUMENTS_MOUNT_FOLDER,
                        'OrderService',
                        str(self.order.user_id),
                        str(self.order.id),
                        document.file_name),
                    f"{document.file_name}"
                )
        return os.path.join(
            settings.MEDIA_URL,
            'OrderService',
            str(self.order.user_id),
            str(self.order.id),
            file_zip_name
        )

    def execute(self, cead_ids: List[int], application_id: int, user_id: int,
                user_ip_address: str, lang_code: str) -> ServiceExecuteResult:
        translation.activate(lang_code)
        self.cead_ids = cead_ids
        self.application_id = application_id
        self.user_id = user_id
        self.user_ip_address = user_ip_address

        # Получение данных заявки
        self._set_application()

        # Проверка есть ли доступ у пользователя к этой заявке
        user = get_user_or_anonymous(user_id)
        if not user_has_access_to_docs(user, self.application_data):
            return ServiceExecuteResult(
                status='error',
                error=ServiceExecuteResultError(
                    error_type='no_access'
                )
            )

        # Получение списка всех документов заявки
        self._set_application_documents()

        # Проверка все ли документы, запрошенные пользователем, входят в список документов заявки
        if not self._check_correct_cead_ids():
            return ServiceExecuteResult(
                status='error',
                error=ServiceExecuteResultError(
                    error_type='wrong_id_doc_cead_list'
                )
            )

        # Проверка все ли документы, запрошенные пользователем, доступны для загрузки
        if self.application_data['search_data']['obj_state'] == 1:
            self._set_docs_wo_receive_date()
            if len(self.documents_wo_receive_date) > 0:
                if len(self.cead_ids) == 1:
                    message = _('Завантаження неможливе, оскільки документ не був отриманий адресатом.')
                else:
                    message = _('Завантаження неможливе, оскільки у списку для завантаження є документ(и), '
                                'що не був(ли) отримані адресатом:')
                    for doc in self.documents_wo_receive_date:
                        message = f"{message}<br>- {doc.title} ({doc.reg_number})"

                return ServiceExecuteResult(
                    status='error',
                    error=ServiceExecuteResultError(
                        error_type='no_receive_date',
                        message=message
                    )
                )

        # Создание заказа
        self._create_order()
        order_result = self._wait_order_completed()
        if not order_result:
            return ServiceExecuteResult(
                status='error',
                error=ServiceExecuteResultError(
                    error_type='order_fail'
                )
            )

        # Формирование архива с документами
        zip_path = self._create_zip()

        # Возврат успешного результата
        return ServiceExecuteResult(
            status='success',
            data={
                'file_path': zip_path
            }
        )
