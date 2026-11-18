import six
import datetime
from django.contrib.auth.models import User, AnonymousUser

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable


def iterable(arg):
    """Возвращает признак того, является ли объект итерируемым."""
    return (
            isinstance(arg, Iterable)
            and not isinstance(arg, six.string_types)
    )


def get_datetime_now_str() -> str:
    return datetime.datetime.now().strftime("%y%m%d_%H%M%S")


def get_unique_filename(prefix: str = '') -> str:
    """Возвращает уникальное имя файла без расширения."""
    suffix = get_datetime_now_str()
    return "_".join([prefix, suffix]).replace('/', '_').replace(' ', '_')


def get_user_or_anonymous(user_id):
    """Возвращает пользователя по его id или возвращает анонимного юзера, если он не найден."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = AnonymousUser()

    return user


def get_client_ip(request):
    """Возвращает IP-адрес пользователя."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
