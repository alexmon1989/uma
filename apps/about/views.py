from django.shortcuts import render
from .models import About


def about(request):
    """Отображает страницу О нас"""
    data, created = About.objects.get_or_create()
    return render(request, 'about/about.html', {'data': data})
