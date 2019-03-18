from django.shortcuts import render
from .models import Help


def help_page(request):
    """Отображает страницу Помощь"""
    data, created = Help.objects.get_or_create()
    lang = request.LANGUAGE_CODE
    return render(
        request,
        'help/help.html',
        {
            'title': getattr(data, f"title_{lang}"),
            'content': getattr(data, f"content_{lang}")
        }
    )
