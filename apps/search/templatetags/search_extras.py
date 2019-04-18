from django import template
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from ..models import ObjType
from ..utils import filter_bad_apps

register = template.Library()


@register.filter
def get_person_name(value):
    values = list(value.to_dict().values())
    return values[0]


@register.filter
def get_person_country(value):
    values = list(value.to_dict().values())
    return values[1]


@register.inclusion_tag('search/advanced/_partials/inv_um_item.html')
def inv_um_item(hit, item_num):
    biblio_data = hit.Claim if hit.search_data.obj_state == 1 else hit.Patent
    return {'biblio_data': biblio_data, 'hit': hit, 'item_num': item_num}


@register.inclusion_tag('search/advanced/_partials/ld_item.html')
def ld_item(hit, item_num):
    biblio_data = hit.Claim if hit.search_data.obj_state == 1 else hit.Patent
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
def registration_status(status):
    return {'status': status}


@register.simple_tag
def user_can_watch_docs(user):
    return user.is_superuser or user.groups.filter(name='Посадовці (чиновники)').exists()


@register.simple_tag
def documents_count():
    """Возвращает количество документов доступных для поиска"""
    client = Elasticsearch(settings.ELASTIC_HOST)
    qs = Q('query_string', query='*')
    qs = filter_bad_apps(qs)
    s = Search(using=client, index='uma').query(qs)
    return s.count()


@register.simple_tag
def get_field(ipc_code, ipc_fields):
    """Ищет поле ipc_code в ipc_fields и возвращает его."""
    for field in ipc_fields:
        if ipc_code == field['ipc_code_short']:
            return field
    return None
