import json
import uuid

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import (
    CertificateService,
    IITProxyService,
    IITSignatureCheckService,
    get_enabled_auth_methods,
)


def logout_view(request):
    """Логаут пользователя."""
    logout(request)
    messages.add_message(request, messages.SUCCESS, _("Вихід успішний."))
    return HttpResponseRedirect("/")


def login_view(request):
    """Страница логина пользователей."""
    if request.user.is_authenticated:
        return redirect("home:index")

    enabled_methods = get_enabled_auth_methods()
    has_ds = bool({"file", "token"} & set(enabled_methods))

    if has_ds:
        request.session["secret"] = uuid.uuid4().hex
    else:
        request.session.pop("secret", None)

    context = {
        "auth_methods_json": json.dumps(enabled_methods),
        "has_ds": has_ds,
    }
    return render(request, "my_auth/login/login.html", context)


@require_POST
def login_ds(request):
    """Оброблює запит на авторизацію за допомогою цифрового підпису."""
    enabled_methods = get_enabled_auth_methods()
    key_type = request.POST.get("key_type") or "file"
    required_method = "token" if key_type == "hardware" else "file"
    if required_method not in enabled_methods:
        return JsonResponse(
            {"is_logged": 0, "error": _("Цей спосіб авторизації вимкнено.")},
            status=403,
        )

    secret = request.session.get("secret")
    if not secret:
        return JsonResponse({"is_logged": 0})

    # Перевірка валідності ЕЦП та отримання/створення сертифіката
    signature_check_service = IITSignatureCheckService()
    certificate_service = CertificateService(
        signature_check_service=signature_check_service
    )
    cert = certificate_service.get_or_create_from_signed_data(request.POST, secret)

    if cert:
        user = authenticate(certificate=cert)
        if user is not None:
            request.session.pop("secret", None)
            login(request, user)
            request.session["auth_key_type"] = cert.key_media_type
            if not request.POST.get("remember_me"):
                request.session.set_expiry(0)
                request.session.modified = True
            messages.add_message(request, messages.SUCCESS, _("Авторизація успішна."))
            return JsonResponse({"is_logged": 1})
    return JsonResponse({"is_logged": 0})


@require_POST
def login_password(request):
    """Обработчик асинхронного запроса на авторизацию по логину и паролю."""
    if "password" not in get_enabled_auth_methods():
        return JsonResponse(
            {"is_logged": 0, "error": _("Авторизація за логіном та паролем вимкнена.")},
            status=403,
        )

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "")

    if not username or not password:
        return JsonResponse(
            {"is_logged": 0, "error": _("Будь ласка, вкажіть логін та пароль.")}
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({"is_logged": 0, "error": _("Невірний логін або пароль.")})

    login(request, user)
    if not request.POST.get("remember_me"):
        request.session.set_expiry(0)
        request.session.modified = True

    messages.add_message(request, messages.SUCCESS, _("Авторизація успішна."))

    nxt = request.POST.get("next")
    if not (
        nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()})
    ):
        nxt = "/"

    return JsonResponse({"is_logged": 1, "next": nxt})


@csrf_exempt
def proxy_handler_view(request):
    """Обробник проксі-запитів для ІІТ ЕЦП."""
    if not bool({"file", "token"} & set(get_enabled_auth_methods())):
        return HttpResponse("Forbidden", status=403)
    return IITProxyService(request).process()
