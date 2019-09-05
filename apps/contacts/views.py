from django.shortcuts import render
from .models import ContactsPage


def contacts(request):
    """Отображает страницу Контакты"""
    data, created = ContactsPage.objects.get_or_create()
    lang = request.LANGUAGE_CODE
    return render(
        request,
        'contacts/contacts.html',
        {
            'title': getattr(data, f"title_{lang}"),
            'content': getattr(data, f"content_{lang}"),
            'operating_mode': getattr(data, f"operating_mode_{lang}"),
            'lunch_break': getattr(data, f"lunch_break_{lang}"),
            'data': data
        }
    )
