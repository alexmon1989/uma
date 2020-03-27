from django.http import HttpResponseBadRequest


def require_ajax(view_func):
    """Return a bad request instance if the view is not using AJAX
    function -- the view
    """

    def wrap(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return view_func(request, *args, **kwargs)

    wrap.__doc__ = view_func.__doc__
    wrap.__name__ = view_func.__name__
    return wrap
