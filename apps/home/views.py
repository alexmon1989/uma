from django.shortcuts import redirect, reverse


def index(request):
    """Отображает главную страницу."""
    # Переадресация на страницу простого поиска
    return redirect(reverse('search:simple'))
