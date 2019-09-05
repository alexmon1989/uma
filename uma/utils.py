import collections
import six
import datetime
from django.contrib.auth.models import User, AnonymousUser


def iterable(arg):
    """Возвращает признак того, является ли объект итерируемым."""
    return (
            isinstance(arg, collections.Iterable)
            and not isinstance(arg, six.string_types)
    )


def get_unique_filename(prefix=''):
    """Возвращает уникальное имя файла без расширения."""
    suffix = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
    return "_".join([prefix, suffix])


def get_user_or_anonymous(user_id):
    """Возвращает пользователя по его id или возвращает анонимного юзера, если он не найден."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        user = AnonymousUser()

    return user
