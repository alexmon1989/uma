from django.shortcuts import render
from .models import About


def about(request):
    """Отображает страницу О нас"""
    data, created = About.objects.get_or_create()
    lang = request.LANGUAGE_CODE
    return render(
        request,
        'about/about.html',
        {
            'title': getattr(data, f"title_{lang}"),
            'content': getattr(data, f"content_{lang}")
        }
    )
