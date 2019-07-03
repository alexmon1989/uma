from django import template
from django.urls import translate_url
from datetime import datetime
import urllib.parse

register = template.Library()


@register.simple_tag(takes_context=True)
def change_language(context, lang=None, *args, **kwargs):
    path = context['request'].get_full_path()
    return translate_url(path, lang)


@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.simple_tag
def replace_and_urlencode(get_params, field, value):
    get_params[field] = value
    return urllib.parse.urlencode(get_params, doseq=True)


@register.filter
def urlencode_dict(data):
    return urllib.parse.urlencode(data, doseq=True)


@register.filter
def get(mapping, key):
    try:
        return mapping[key]
    except KeyError:
        return ''


@register.filter
def parse_date(value):
    return datetime.strptime(value, '%Y-%m-%d')


@register.filter
def get_list(dictionary, key):
    return dictionary.getlist(key)


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

