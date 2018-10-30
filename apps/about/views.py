from django.shortcuts import render


def about(request):
    """Отображает страницу О нас"""
    return render(request, 'about/about.html')
