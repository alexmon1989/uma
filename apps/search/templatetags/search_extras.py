from django import template
from django.conf import settings
from django.db.models import F
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from ..models import ObjType, SortParameter, IndexationProcess
from ..utils import filter_bad_apps, user_has_access_to_docs as user_has_access_to_docs_, filter_unpublished_apps

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
    status = 'gray'
    if hit['Document']['idObjType'] in (1, 2, 3):
        if hit['Document']['RegistrationStatus'] == 'A':
            status = 'green'
        elif hit['Document']['RegistrationStatus'] == 'N':
            status = 'red'
        elif hit['Document']['RegistrationStatus'] == 'T':
            status = 'yellow'
    elif hit['Document']['idObjType'] == 4:
        status = 'green'

        red_transaction_types = [
            'TerminationNoRenewalFee',
            'TotalTerminationByOwner',
            'TotalInvalidationByCourt',
            'TotalTerminationByCourt',
            'TotalInvalidationByAppeal',
        ]

        if hit.get('TradeMark', {}).get('Transactions'):
            last_transaction_type = \
                hit['TradeMark']['Transactions']['Transaction'][len(hit['TradeMark']['Transactions']['Transaction']) - 1]['@type']

            if last_transaction_type in red_transaction_types:
                status = 'red'

    elif hit['Document']['idObjType'] == 6:
        status = 'green'

        red_transaction_types = [
            'Termination',
            'TerminationByAppeal',
            'TerminationNoRenewalFee',
            'TotalInvalidationByAppeal',
            'TotalInvalidationByCourt',
            'TotalTerminationByOwner',
        ]

        if hit.get('Design', {}).get('Transactions'):
            last_transaction_type = \
                hit['Design']['Transactions']['Transaction'][len(hit['Design']['Transactions']['Transaction']) - 1]['@type']

            if last_transaction_type in red_transaction_types:
                status = 'red'

    return {'status': status, 'hit': hit}

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
