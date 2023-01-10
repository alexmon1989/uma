import datetime
from typing import List, Optional
import time
import copy

from django.utils.translation import gettext as _
from django.conf import settings

from ..models import IpcAppList
from ...bulletin import services as bulletin_services


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
