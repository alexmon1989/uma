from django.shortcuts import render
from .models import Help


def help_page(request):
    """Отображает страницу Помощь"""
    data, created = Help.objects.get_or_create()
    return render(request, 'help/help.html', {'data': data})
