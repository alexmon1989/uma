from django.shortcuts import render, redirect, reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from apps.my_auth.forms import AuthFormSimple
from .utils import get_certificate
import random
import string


def logout_view(request):
    """Логаут пользователя."""
    logout(request)
    messages.add_message(
        request,
        messages.SUCCESS,
        'Вихід успішний.'
    )
    return HttpResponseRedirect('/')


def login_view(request):
    """Страница логина пользователей."""
    request.session['secret'] = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(32)
    )
    return render(
        request,
        'my_auth/login/login.html',
        {
            'form_login_password': AuthFormSimple(),
        }
    )


@require_POST
def login_ds(request):
    """Обработчик запроса на авторизацию по ЭЦП."""
    # Проверка валидности ЭЦП
    cert = get_certificate(request.POST, request.session['secret'])

    if cert:
        user = authenticate(certificate=cert)
        if user is not None:
            login(request, user)
            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)
                request.session.modified = True
            messages.add_message(
                request,
                messages.SUCCESS,
                'Авторизація успішна.'
            )
            return JsonResponse({
                'is_logged': 1
            })
    return JsonResponse({
        'is_logged': 0
    })


@require_POST
def login_password(request):
    """Обработчик запроса на авторизацию по логину и паролю."""
    form = AuthFormSimple(request.POST, request)

    if form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user is not None:
            login(request, user)
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)
                request.session.modified = True
            nxt = request.POST.get('next')
            if nxt:
                return redirect(nxt)
            return redirect('/')
        else:
            return redirect(reverse('auth:login'))
    else:
        return render(
            request,
            'my_auth/login/login.html',
            {
                'form_login_password': form,
            }
        )
