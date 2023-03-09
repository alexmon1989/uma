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
    return "_".join([prefix, suffix]).replace('/', '_')


def get_user_or_anonymous(user_id):
    """Возвращает пользователя по его id или возвращает анонимного юзера, если он не найден."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = AnonymousUser()

    return user
