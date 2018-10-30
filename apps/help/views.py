from django.shortcuts import render


def help_page(request):
    """Отображает страницу Помощь"""
    return render(request, 'help/help.html')
