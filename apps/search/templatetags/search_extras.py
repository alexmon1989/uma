from django import template
from django.conf import settings
from django.db.models import F
from django.utils.translation import gettext as _
from ..models import ObjType, SortParameter, IndexationProcess, PaidServicesSettings
from ..utils import (user_has_access_to_docs as user_has_access_to_docs_, get_registration_status_color,
                     user_has_access_to_tm_app)

register = template.Library()


@register.filter
def get_person_name(value):
    values = list(value.values())
    return values[0]


@register.filter
def get_person_country(value):
    values = list(value.values())
    return values[1]


@register.inclusion_tag('search/advanced/_partials/inv_um_item.html', takes_context=True)
def inv_um_item(context, hit, item_num):
    biblio_data = hit.get('Claim') if hit['search_data']['obj_state'] == 1 else hit.get('Patent')
    return {'biblio_data': biblio_data, 'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/ld_item.html', takes_context=True)
def ld_item(context, hit, item_num):
    biblio_data = hit['Claim'] if hit['search_data']['obj_state'] == 1 else hit['Patent']
    return {'biblio_data': biblio_data, 'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/tm_item.html', takes_context=True)
def tm_item(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/id_item.html', takes_context=True)
def id_item(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.inclusion_tag('search/advanced/_partials/qi_item.html', takes_context=True)
def qi_item(context, hit, item_num):
    return {'hit': hit, 'item_num': item_num, 'request': context['request']}


@register.filter
def document_path(file_name):
    return file_name.replace("\\\\bear\share\\", settings.MEDIA_URL).replace("\\", "/")


@register.filter
def get_image_url(file_path, image_name):
    splitted_path = file_path.replace("\\", "/").split('/')
    splitted_path_len = len(splitted_path)

    return f"{settings.MEDIA_URL}/" \
           f"{splitted_path[splitted_path_len-4]}" \
           f"/{splitted_path[splitted_path_len-3]}/" \
           f"{splitted_path[splitted_path_len-2]}/{image_name}"


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
def user_can_watch_docs(user):
    return user.is_superuser or user.groups.filter(name='Посадовці (чиновники)').exists()


@register.simple_tag
def documents_count():
    """Возвращает количество документов доступных для поиска"""
    record = IndexationProcess.objects.order_by('-pk').filter(finish_date__isnull=False)
    doc_count = None
    if record.count() > 0:
        doc_count = record.first().documents_in_index_shared
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
    return list(filter(lambda x: x['DOCRECORD'].get('DOCREGNUMBER') or x['DOCRECORD'].get('DOCBARCODE'), documents))


@register.simple_tag
def user_has_access_to_app(user, hit):
    """Возвращает признак того, что пользователю доступна платная заявка."""
    return user_has_access_to_tm_app(user, hit)


@register.simple_tag
def is_paid_services_enabled():
    """Возвращает значения того включены ли платные услуги."""
    paid_services_settings, created = PaidServicesSettings.objects.get_or_create()
    return paid_services_settings.enabled


@register.inclusion_tag('search/templatetags/app_stages_tm.html')
def app_stages_tm(app):
    """Отображает стадии заявки (градусник)."""
    mark_status_code = int(app['Document'].get('MarkCurrentStatusCodeType', 0))
    is_stopped = app['Document'].get('RegistrationStatus') == 'Діловодство за заявкою припинено'

    if app['search_data']['obj_state'] == 2:
        stages_statuses = ['done' for _ in range(6)]
    else:
        stages_statuses = ['not-active' for _ in range(6)]

        for i, s in enumerate(stages_statuses):
            if mark_status_code >= (i + 1) * 1000:
                stages_statuses[i] = 'done'
            else:
                if is_stopped:
                    stages_statuses[i] = 'not-active'
                    stages_statuses[i-1] = 'stopped'
                else:
                    stages_statuses[i] = 'current'
                break

    stages = [
        {
            'title': _('Знак для товарів і послуг зареєстровано'),
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
        'obj_state': app['search_data']['obj_state']
    }


@register.inclusion_tag('search/templatetags/app_stages_id.html')
def app_stages_id(app):
    """Отображает стадии заявки (градусник)."""
    design_status_code = int(app['Document'].get('DesignCurrentStatusCodeType', 0))
    is_stopped = app['Document'].get('RegistrationStatus') == 'Діловодство за заявкою припинено'

    if app['search_data']['obj_state'] == 2:
        stages_statuses = ['done' for _ in range(5)]
    else:
        stages_statuses = ['not-active' for _ in range(5)]
        marks = [1000, 2000, 4000, 5000, 5002]

        for i, s in enumerate(stages_statuses):
            if design_status_code >= marks[i]:
                stages_statuses[i] = 'done'
            else:
                if is_stopped:
                    stages_statuses[i] = 'not-active'
                    stages_statuses[i-1] = 'stopped'
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
        'app': app
    }
