import datetime

from django import template
from django.conf import settings
from django.db.models import F
from django.utils.translation import gettext as _
from ..models import ObjType, SortParameter, IndexationProcess, PaidServicesSettings
from ..utils import (user_has_access_to_docs as user_has_access_to_docs_, get_registration_status_color,
                     get_fixed_mark_status_code)
from apps.bulletin.services import bulletin_get_number_by_date, bulletin_get_number_with_year_by_date
import re
from typing import List

register = template.Library()


@register.filter
def get_person_name(value):
    try:
        del value['EDRPOU']
    except KeyError:
        pass
    values = list(value.values())
    return values[0] if len(values[0]) > len(values[1]) else values[1]


@register.filter
def get_person_country(value):
    try:
        del value['EDRPOU']
    except KeyError:
        pass
    values = list(value.values())
    return values[1] if len(values[1]) < len(values[0]) else values[0]


@register.inclusion_tag('search/advanced/_partials/inv_um_item.html', takes_context=True)
def inv_um_item(context, hit, item_num):
    biblio_data = hit.get('Claim') if hit['search_data']['obj_state'] == 1 else hit.get('Patent')
    return {'biblio_data': biblio_data, 'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/cap_item.html', takes_context=True)
def cap_item(context, hit, item_num):
    biblio_data = hit.get('Patent_Certificate')
    return {'biblio_data': biblio_data, 'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/ld_item.html', takes_context=True)
def ld_item(context, hit, item_num):
    biblio_data = hit['Claim'] if hit['search_data']['obj_state'] == 1 else hit['Patent']
    return {'biblio_data': biblio_data, 'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/tm_item.html', takes_context=True)
def tm_item(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/tm_item_madrid.html', takes_context=True)
def tm_item_madrid(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/id_item.html', takes_context=True)
def id_item(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/qi_item.html', takes_context=True)
def qi_item(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/copyright_item.html', takes_context=True)
def copyright_item(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/agreement_item.html', takes_context=True)
def agreement_item(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.filter
def document_path(file_name):
    return file_name.replace("\\\\bear\share\\", settings.MEDIA_URL).replace("\\", "/")


@register.filter
def get_image_url(file_path, image_name):
    splitted_path = file_path.replace("\\", "/").split('/')
    splitted_path_len = len(splitted_path)

    return f"{settings.MEDIA_URL}/" \
           f"{splitted_path[splitted_path_len - 4]}" \
           f"/{splitted_path[splitted_path_len - 3]}/" \
           f"{splitted_path[splitted_path_len - 2]}/{image_name}"


@register.filter
def get_image_url_madrid_tm(file_path, image_name):
    splitted_path = file_path.replace("\\", "/").split('/')
    splitted_path_len = len(splitted_path)

    return f"{settings.MEDIA_URL}/" \
           f"{splitted_path[splitted_path_len - 5].upper()}/" \
           f"{splitted_path[splitted_path_len - 4]}/" \
           f"{splitted_path[splitted_path_len - 3]}/" \
           f"{splitted_path[splitted_path_len - 2]}/{image_name}"


@register.inclusion_tag('search/detail/document_pdf.html')
def document_pdf(path, height=500):
    return {'document_path': path, 'height': height}


@register.simple_tag
def obj_type_title(id, lang):
    obj_type = ObjType.objects.get(id=id)
    if lang == 'ua':
        return obj_type.obj_type_ua
    else:
        return obj_type.obj_type_en


@register.inclusion_tag('search/templatetags/registration_status.html')
def registration_status(hit):
    """Выводит статус охранного документа (зелёный, желтый, красный)."""
    return {'hit': hit}


@register.simple_tag
def registration_status_color(hit):
    """Возвращает статус охранного документа (зелёный, желтый, красный)."""
    return get_registration_status_color(hit)


@register.simple_tag
def is_first_year_paid_inv_um(collections: List[dict]) -> bool:
    """Возвращает признак того что оплачен первый сбор поддержки действия патента."""
    for item in collections:
        # Если сбор найден, то производится проверка оплачен ли он
        if re.search(r'Збір за \d+ рік чинності', item['CLRECORD']['CLNAME']) \
                and bool(item['CLRECORD'].get('CLDATEFACT')):
            return True
    return False


@register.simple_tag
def publication_inv_um_older_than_months(hit: dict, months: int) -> bool:
    """Возвращает признак тарше ли публикация колическва месяцев months."""
    pub_date = datetime.datetime.strptime(hit['Patent']['I_45.D'][0], '%Y-%m-%d')
    four_months = pub_date + datetime.timedelta(days=(365.25 / 12) * months)
    return datetime.datetime.now() > four_months


@register.simple_tag
def user_can_watch_docs(user):
    return user.is_superuser or user.groups.filter(name='Посадовці (чиновники)').exists()


@register.simple_tag
def documents_count():
    """Возвращает количество документов доступных для поиска"""
    record = IndexationProcess.objects.order_by('-pk').filter(finish_date__isnull=False)
    doc_count = None
    if record.count() > 0:
        doc_count = record.first().documents_in_index
    return doc_count or '-'


@register.simple_tag
def last_finished_indexation_date():
    """Возвращает дату и время последней законченной индексации."""
    p = IndexationProcess.objects.order_by('-pk').filter(finish_date__isnull=False)
    if p.count() > 0:
        return p.first().finish_date
    return '-'


@register.simple_tag
def get_field(ipc_code, ipc_fields):
    """Ищет поле ipc_code в ipc_fields и возвращает его."""
    for field in ipc_fields:
        if ipc_code == field['ipc_code_short']:
            return field
    return None


@register.inclusion_tag('search/templatetags/sort_params.html', takes_context=True)
def sort_params(context):
    """Отображает элемент для выбора параметра сортировки результатов поиска."""
    return {
        'sort_params': SortParameter.objects.filter(
            is_enabled=True
        ).order_by(
            '-weight'
        ).annotate(
            title=F(f"title_{context['request'].LANGUAGE_CODE}")
        ).values(
            'title',
            'value'
        ),
        'request_get_params': context['get_params']
    }


@register.simple_tag
def user_has_access_to_docs(user, id_app_number):
    """Возвращает признак доступности документа(ов)."""
    return user_has_access_to_docs_(user, id_app_number)


@register.filter
def filter_bad_documents(documents):
    """Исключает из списка документов документы без даты регистрации и barcode"""
    if documents:
        return list(filter(lambda x: (x['DOCRECORD'].get('DOCREGNUMBER')
                                      or x['DOCRECORD'].get('DOCBARCODE')
                                      or x['DOCRECORD'].get('DOCSENDINGDATE'))
                                     and 'службова' not in x['DOCRECORD'].get('DOCTYPE', '').lower()
                                     and 'звіт про інформаційний пошук' not in x['DOCRECORD'].get('DOCTYPE', '').lower()
                                     and not x['DOCRECORD'].get('DOCREGNUMBER', '').lower().startswith('вн'),
                           documents))


@register.simple_tag
def is_paid_services_enabled():
    """Возвращает значения того включены ли платные услуги."""
    paid_services_settings, created = PaidServicesSettings.objects.get_or_create()
    return paid_services_settings.enabled


@register.inclusion_tag('search/templatetags/app_stages_tm.html')
def app_stages_tm(app):
    """Отображает стадии заявки (градусник) для знаков для товаров и услуг."""
    if app['TradeMark'].get('TrademarkDetails', {}).get('stages'):  # Заявки из новой системы
        stages = list(map(lambda x: {'title': x['title'], 'status': x['status'].replace(';', '')},
                          app['TradeMark']['TrademarkDetails']['stages']))

        # Fix
        prev_status = ''
        for stage in stages[::-1]:
            if stage["title"] == "Встановлення дати подання" \
                    and app['TradeMark'].get('TrademarkDetails', {}).get('Code_441'):
                if stage['status'] == 'current':
                    stages[3]['status'] = 'current'
                stage['status'] = 'done'
                continue

            if stage['status'] == 'current' == prev_status \
                    or (stage['status'] in ('done', 'current', 'stopped',)
                        and prev_status in ('current', 'not-active', 'stopped')):
                stage['status'] = 'not-active'

            prev_status = stage['status']

        is_stopped = app['TradeMark']['TrademarkDetails']['application_status'] == 'stopped'
        return {
            'stages': stages,
            'is_stopped': is_stopped,
            'obj_state': app['search_data']['obj_state'],
            'mark_status_code': len(list(filter(lambda x: x['status'] == 'done', stages))) * 1000,
        }

    # mark_status_code = int(app['Document'].get('MarkCurrentStatusCodeType', 0))
    mark_status_code = get_fixed_mark_status_code(app)
    is_stopped = app['Document'].get('RegistrationStatus') == 'Діловодство за заявкою припинено' \
                 or mark_status_code == 8000

    if app['search_data']['obj_state'] == 2:
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
            for doc in app['TradeMark']['DocFlow']['Documents']:
                if 'Т-08' in doc['DocRecord'].get('DocFlow', {}).get('Documents', []):
                    stages_statuses[4] = 'current'
                    stages_statuses[3] = 'done'
                    break

        # Если есть форма Т-05, то "Формальна експертиза" пройдена (для случая если делопроизводство остановлено)
        if is_stopped:
            for doc in app['TradeMark'].get('DocFlow', {}).get('Documents', []):
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

    return {
        'stages': stages,
        'is_stopped': is_stopped,
        'obj_state': app['search_data']['obj_state'],
        'mark_status_code': mark_status_code,
    }


@register.inclusion_tag('search/templatetags/app_stages_id.html')
def app_stages_id(app):
    """Отображает стадии заявки (градусник) для пром. образцов."""
    if app['Design'].get('DesignDetails', {}).get('stages'):  # Заявки из новой системы
        stages = list(map(lambda x: {'title': x['title'], 'status': x['status'].replace(';', '')},
                          app['Design']['DesignDetails']['stages']))
        is_stopped = app['Design']['DesignDetails']['application_status'] == 'stopped'

        # Fix
        prev_status = ''
        for stage in stages[::-1]:
            if stage['status'] == 'current' == prev_status or (
                    stage['status'] in ('done', 'current', 'stopped',) and prev_status in ('current', 'not-active')):
                stage['status'] = 'not-active'
            prev_status = stage['status']

        return {
            'stages': stages,
            'is_stopped': is_stopped,
            'app': app,
            'design_status_code': len(list(filter(lambda x: x['status'] == 'done', stages))) * 1000 + 1000,
        }

    design_status_code = int(app['Document'].get('DesignCurrentStatusCodeType', 0))
    is_stopped = app['Document'].get('RegistrationStatus') == 'Діловодство за заявкою припинено'

    if app['search_data']['obj_state'] == 2:
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

    return {
        'stages': stages,
        'is_stopped': is_stopped,
        'app': app,
        'design_status_code': design_status_code,
    }


@register.inclusion_tag('search/templatetags/app_stages_kzpt.html')
def app_stages_kzpt(app):
    """Отображает стадии заявки (градусник) для знаков для КЗПТ."""
    if app['search_data']['obj_state'] == 1:
        stages_statuses = app['Geo']['GeoDetails']['stages']
    else:
        stages_statuses = [{'status': 'done'} for x in range(5)]
    stages = [
        {
            'title': _('Географічне зазначення зареєстровано'),
            'status': stages_statuses[4]['status'],
        },
        {
            'title': _('Підготовка до державної реєстрації та публікації'),
            'status': stages_statuses[3]['status'],
        },
        {
            'title': _('Експертиза заявки'),
            'status': stages_statuses[2]['status'],
        },
        {
            'title': _('Встановлення дати подання'),
            'status': stages_statuses[1]['status'],
        },
        {
            'title': _('Реєстрація первинних документів, попередня експертиза та введення відомостей до бази даних'),
            'status': stages_statuses[0]['status'],
        },
    ]

    return {
        'stages': stages,
        'is_stopped': app['Geo']['GeoDetails'].get('application_status') == 'stopped',
        'obj_state': app['search_data']['obj_state'],
    }


@register.inclusion_tag('search/templatetags/app_stages_inv_um.html')
def app_stages_inv_um(app):
    """Отображает стадии заявки (градусник) для изобретений и полезных моделей."""
    # Состояние делопроизводства
    is_stopped = False
    doc_types = [doc['DOCRECORD']['DOCTYPE'] for doc in app['DOCFLOW'].get('DOCUMENTS', [])
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
    for stage in app['DOCFLOW'].get('STAGES', []):
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
        elif stage['STAGERECORD']['STAGE'] == 'Кваліфікаційна експертиза' \
                and stage['STAGERECORD'].get('ENDDATE') \
                and app['search_data']['obj_state'] == 1:
            for doc_type in doc_types:
                if '[В9]' in doc_type:
                    done_stages.append(stage['STAGERECORD']['STAGE'])
                    break
        elif stage['STAGERECORD'].get('ENDDATE'):
            done_stages.append(stage['STAGERECORD']['STAGE'])

    # Коды сборов
    cl_codes = []
    for stage in app['DOCFLOW'].get('COLLECTIONS', []):
        if stage['CLRECORD'].get('CLCODE'):
            cl_codes.append(stage['CLRECORD']['CLCODE'])

    # Стадии делопроизводства по заявке
    stages = [
        {
            'title': _('Патент зареєстровано'),
            'status': 'done' if app['search_data']['obj_state'] == 2
                                or 'Підтримка чинності' in done_stages
            else 'not-active'
        },
        {
            'title': _('Підготовка до державної реєстрації та публікації'),
            'status': 'done' if app['search_data']['obj_state'] == 2
                                or 'Підготовка заявки до реєстрації патенту' in done_stages
            else 'not-active'
        },
        {
            'title': _('Очікування документа про сплату державного мита'),
            'status': 'done' if app['search_data']['obj_state'] == 2
                                or '19994' in cl_codes or '19996' in cl_codes
            else 'not-active'
        },
        {
            'title': _('Кваліфікаційна експертиза'),
            'status': 'done' if app['search_data']['obj_state'] == 2 or 'Кваліфікаційна експертиза' in done_stages
            else 'not-active'
        },
        {
            'title': _('Очікування клопотання про проведення кваліфікаційної експертизи'),
            'status': 'done' if app['search_data']['obj_state'] == 2
                                or 'Очікування клопотання та збору щодо КЕ' in done_stages
            else 'not-active'
        },
        {
            'title': _('Формальна експертиза'),
            'status': 'done' if app['search_data']['obj_state'] == 2
                                or 'Формальна експертиза заявок на винаходи і корисні моделі' in done_stages
            else 'not-active'
        },
        {
            'title': _('Встановлення дати подання'),
            'status': 'done' if app['search_data']['obj_state'] == 2
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
    if app['Document']['idObjType'] == 2:
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
                    if stages[i - 1]['status'] == 'not-used':
                        # Для полезных моделей пропускаются два неиспользуемых этапа
                        stages[i - 3]['status'] = 'current'
                    else:
                        stages[i - 1]['status'] = 'current'
            break

    return {
        'stages': stages,
        'is_stopped': is_stopped,
        'app': app,
    }


@register.simple_tag
def id_has_colors(hit):
    """Возвращает признак наличия заявленных цветов у пром. образца."""
    for item in hit['Design'].get('DesignDetails', {}).get('DesignSpecimenDetails', {}):
        if item.get('Colors'):
            return True
    return False


@register.filter
def filter_tm_id_docs_direction(documents, direction):
    """Возвращает только входящие/исходящие документы ТМ."""
    if documents:
        return list(filter(lambda x: x.get('DocRecord', {}).get('DocDirection') == direction, documents))
    return list()


@register.filter
def remove_inn(s):
    """Удаляет из строки ИНН (10-значное число)."""
    s = re.sub(r'(?<!\w)\d{6,10}', '', s)
    s = s.replace('; ; ', '')
    s = s.strip()

    # Также удаляется запятая, если строка ею заканчивается
    if s.endswith(','):
        s = s[:len(s) - 2]

    # Также удаляется точка с запятой, если строка ею заканчивается
    if s.endswith(';'):
        s = s[:len(s) - 2]

    return s


@register.simple_tag()
def bulletin_number_by_date(value) -> str | int:
    """Возвращает номер бюлетня из таблицы БД."""
    bul_num = bulletin_get_number_by_date(value)
    if bul_num:
        return bul_num
    return ''


@register.simple_tag()
def bulletin_number_with_year_by_date(value) -> str | int:
    """Возвращает номер бюлетня с годом из таблицы БД."""
    bul_num = bulletin_get_number_with_year_by_date(value)
    if bul_num:
        return bul_num
    return ''


@register.simple_tag()
def designer_should_be_publicated_in_transaction(designer_name: str, designer_biblio: dict) -> bool:
    """Повертає ознаку чи має ім'я автора публікуватися у сповіщенні.

       Функція порівнює ім'я автора з тим, що в бібліографії і якщо є співпадіння,
       то повертає ознаку публікації автора з бібліографії
    """
    for designer in designer_biblio['Designer']:
        if designer_name == designer['DesignerAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
            'FreeFormatNameDetails']['FreeFormatNameLine']:
            return designer['Publicated']
    return True
