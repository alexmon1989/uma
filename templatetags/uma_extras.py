from django import template
from django.urls import translate_url
from datetime import datetime
import urllib.parse
from apps.contacts.models import ContactsPage
import json

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
    try:
        return datetime.strptime(value[:10], '%Y-%m-%d')
    except ValueError:
        return value


@register.filter
def get_list(dictionary, key):
    return dictionary.getlist(key)


@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter
def list_of_dicts_unique(l):
    if l is not None:
        return [i for n, i in enumerate(l) if i not in l[n + 1:]]
    return l


@register.filter
def highlight(text, q):
    try:
        index_l = text.lower().index(q.lower())
    except ValueError:
        return text
    else:
        original_text = text[index_l:index_l + len(q)]
        return text[:index_l] + f"<em class='g-bg-yellow'>{original_text}</em>" + text[index_l + len(q):]


@register.inclusion_tag('templatetags/footer_contacts.html', takes_context=True)
def footer_contacts(context):
    contacts, created = ContactsPage.objects.get_or_create()
    return {'contacts': contacts, 'request': context['request']}


@register.simple_tag
def json_to_dict(value):
    return json.loads(value)
