from django import template
from django.conf import settings

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
    return {'hit': hit, 'item_num': item_num}


@register.inclusion_tag('search/advanced/_partials/ld_item.html')
def ld_item(hit, item_num):
    return {'hit': hit, 'item_num': item_num}


@register.filter
def document_path(file_name):
    return file_name.replace("\\\\bear\share\\", settings.MEDIA_URL).replace("\\", "/")


@register.inclusion_tag('search/detail/document_pdf.html')
def document_pdf(path, height=500):
    return {'document_path': path, 'height': height}
