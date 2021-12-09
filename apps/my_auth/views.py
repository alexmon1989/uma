from django.shortcuts import render, redirect, reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from django.views.decorators.http import require_POST
from apps.my_auth.forms import AuthFormDS, AuthFormSimple
from apps.my_auth.models import CertificateOwner, KeyCenter
from EUSignCP import *
from .utils import get_signed_data_info
import random, string

def logout_view(request):
    """Логаут пользователя."""
    logout(request)
    messages.add_message(
        request,
        messages.SUCCESS,
        'Вихід успішний.'
    )
    return HttpResponseRedirect('/')


def get_ca_data(request, pk):
    """Возвращает данные АЦСК в формате JSON."""
    ca = get_object_or_404(KeyCenter, pk=pk)
    return JsonResponse(model_to_dict(ca))


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
            'form_ds': AuthFormDS(),
        }
    )


@require_POST
def login_ds(request):
    """Обработчик запроса на авторизацию по ЭЦП."""
    # Проверка валидности ЭЦП
    sign_info = get_signed_data_info(request.POST['signed_data'],
                                     request.session['secret'],
                                     request.POST['key_center_title'])
    if sign_info:
        try:
            cert = CertificateOwner.objects.get(pszSerial=sign_info['pszSerial'])
        except CertificateOwner.DoesNotExist:
            # Запись данных ключа в БД
            cert = CertificateOwner(
                pszIssuer=sign_info.get('pszIssuer'),
                pszIssuerCN=sign_info.get('pszIssuerCN'),
                pszSerial=sign_info.get('pszSerial'),
                pszSubject=sign_info.get('pszSubject'),
                pszSubjCN=sign_info.get('pszSubjCN'),
                pszSubjOrg=sign_info.get('pszSubjOrg'),
                pszSubjOrgUnit=sign_info.get('pszSubjOrgUnit'),
                pszSubjTitle=sign_info.get('pszSubjTitle'),
                pszSubjState=sign_info.get('pszSubjState'),
                pszSubjFullName=sign_info.get('pszSubjFullName'),
                pszSubjAddress=sign_info.get('pszSubjAddress'),
                pszSubjPhone=sign_info.get('pszSubjPhone'),
                pszSubjEMail=sign_info.get('pszSubjEMail'),
                pszSubjDNS=sign_info.get('pszSubjDNS'),
                pszSubjEDRPOUCode=sign_info.get('pszSubjEDRPOUCode'),
                pszSubjDRFOCode=sign_info.get('pszSubjDRFOCode'),
                pszSubjLocality=sign_info.get('pszSubjLocality'),
            )
            cert.save()
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
            return redirect('/')
        else:
            return redirect(reverse('auth:login'))
    else:
        return render(
            request,
            'my_auth/login/login.html',
            {
                'form_login_password': form,
                'form_ds': AuthFormDS(),
            }
        )
