import os
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict
from apps.my_auth.forms import AuthForm, AuthFormSimple
from apps.my_auth.utils import get_certificate_data, save_file_to_temp, save_file_to_eu_file_store
from apps.my_auth.models import CertificateOwner, KeyCenter


def login_view(request):
    """Логин пользователей."""
    if request.method == 'POST':
        form = AuthForm(request.POST, request.FILES)

        if form.is_valid():
            # Сохранение файла ключа ЭЦП во временный каталог
            key_file_path = save_file_to_temp(request.FILES['key_file'])

            # Сохранение файла сертификата в каталог сертификатов
            cert_file_path = None
            if request.FILES.get('cert_file'):
                cert_file_path = save_file_to_eu_file_store(request.FILES['cert_file'])

            try:
                # Считывание данных ключа
                cert_data = get_certificate_data(key_file_path, form.cleaned_data['password'], form.cleaned_data['ca'])

                # Проверка есть ли этот сертификат в БД
                try:
                    cert = CertificateOwner.objects.get(pszSerial=cert_data['pszSerial'])
                    # Авторизация пользователя
                    user = authenticate(certificate=cert)
                    if user is not None:
                        login(request, user)
                        messages.add_message(
                            request,
                            messages.SUCCESS,
                            'Авторизація успішна.'
                        )
                        return HttpResponseRedirect('/private/')
                    else:
                        messages.add_message(
                            request,
                            messages.INFO,
                            'Ваш профіль поки що не підтверджено адміністратором. Спробуйте пізніше.'
                        )
                except CertificateOwner.DoesNotExist:
                    # Запись данных ключа в БД
                    cert = CertificateOwner(**cert_data)
                    cert.save()
                    messages.add_message(
                        request,
                        messages.SUCCESS,
                        'Ви успішно зареєстровані та зможете увійти у систему '
                        'після підтвердження вашого профілю адміністратором'
                    )
            except RuntimeError as e:
                messages.add_message(request, messages.ERROR, e)
            finally:
                if cert_file_path:
                    os.unlink(cert_file_path)
    else:
        form = AuthForm()

    return render(request, 'my_auth/login.html', {'form': form})


def login_simple_view(request):
    """Логин пользователей."""
    if request.method == 'POST':
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
        form = AuthFormSimple()

    return render(request, 'my_auth/login_simple/login_simple.html', {'form': form})


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
