from django import template
from django.conf import settings
from django.db.models import F
from ..models import ObjType, SortParameter, IndexationProcess
from ..utils import user_has_access_to_docs as user_has_access_to_docs_, get_registration_status_color

register = template.Library()


@register.filter
def get_person_name(value):
    values = list(value.values())
    return values[0]


@register.filter
def get_person_country(value):
    values = list(value.values())
    return values[1]


@register.inclusion_tag('search/advanced/_partials/inv_um_item.html')
def inv_um_item(hit, item_num):
    biblio_data = hit['Claim'] if hit['search_data']['obj_state'] == 1 else hit['Patent']
    return {'biblio_data': biblio_data, 'hit': hit, 'item_num': item_num}


@register.inclusion_tag('search/advanced/_partials/ld_item.html')
def ld_item(hit, item_num):
    biblio_data = hit['Claim'] if hit['search_data']['obj_state'] == 1 else hit['Patent']
    return {'biblio_data': biblio_data, 'hit': hit, 'item_num': item_num}


@register.inclusion_tag('search/advanced/_partials/tm_item.html')
def tm_item(hit, item_num):
    return {'hit': hit, 'item_num': item_num}


@register.inclusion_tag('search/advanced/_partials/id_item.html')
def id_item(hit, item_num):
    return {'hit': hit, 'item_num': item_num}


@register.inclusion_tag('search/advanced/_partials/qi_item.html')
def qi_item(hit, item_num):
    return {'hit': hit, 'item_num': item_num}


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


@register.simple_tag(takes_context=True)
def documents_count(context):
    """Возвращает количество документов доступных для поиска"""
    p = IndexationProcess.objects.order_by('-pk').filter(finish_date__isnull=False)
    doc_count = None
    if p.count() > 0:
        if context['request'].user.is_anonymous or not context['request'].user.is_vip():
            doc_count = p.first().documents_in_index_shared
        else:
            doc_count = p.first().documents_in_index
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
