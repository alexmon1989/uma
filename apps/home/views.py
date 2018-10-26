from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from apps.my_auth.models import CertificateOwner


def index(request):
    """Отображает главную страницу."""
    # Переадресация на страницу простого поиска
    return redirect(reverse('search:simple'))


@login_required
def private_page(request):
    """Отображает закрытую страницу. Доступна после авторизации."""
    try:
        cert = CertificateOwner.objects.get(user=request.user)
    except CertificateOwner.DoesNotExist:
        cert = None
    return render(request, 'home/private.html', {'cert': cert})
