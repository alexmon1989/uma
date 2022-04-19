from django import template

register = template.Library()


@register.simple_tag
def get_splitted_email(item):
    if ',' in item['e_mail']:
        return item['e_mail'].split(',')
    elif ';' in item['e_mail']:
        return item['e_mail'].split(';')
    else:
        return [item['e_mail']]
