from django import template
from django.conf import settings
from ..models import ObjType

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


@register.filter
def document_path(file_name):
    return file_name.replace("\\\\bear\share\\", settings.MEDIA_URL).replace("\\", "/")


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
