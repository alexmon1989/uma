import collections
import six
import datetime


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
