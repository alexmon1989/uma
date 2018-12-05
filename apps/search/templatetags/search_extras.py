from django import template

register = template.Library()


@register.filter
def get_person_name(value):
    values = list(value.to_dict().values())
    return values[0]


@register.filter
def get_person_country(value):
    values = list(value.to_dict().values())
    return values[1]


@register.inclusion_tag('search/advanced/_partials/inv_um_claim_item.html')
def inv_um_claim_item(hit, item_num):
    return {'hit': hit, 'item_num': item_num}


@register.inclusion_tag('search/advanced/_partials/inv_um_protective_item.html')
def inv_um_protective_item(hit, item_num):
    return {'hit': hit, 'item_num': item_num}
