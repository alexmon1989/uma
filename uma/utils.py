import collections
import six


def iterable(arg):
    """Возвращает признак того, является ли объект итерируемым."""
    return (
            isinstance(arg, collections.Iterable)
            and not isinstance(arg, six.string_types)
    )
