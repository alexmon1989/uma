from django.http import HttpResponseBadRequest
from django.conf import settings
import requests


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


def check_recaptcha(view_func):
    def wrap(request, *args, **kwargs):
        try:
            data = {
                'response': request.GET['token'],
                'secret': settings.RECAPTCHA_SECRET_KEY
            }
        except KeyError:
            return HttpResponseBadRequest()
        resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data, verify=settings.SSL_CERT_FILE)
        result_json = resp.json()
        if not result_json.get('success') or result_json.get('score') < settings.RECAPTCHA_MIN_SCORE:
            return HttpResponseBadRequest()
        return view_func(request, *args, **kwargs)

    wrap.__doc__ = view_func.__doc__
    wrap.__name__ = view_func.__name__
    return wrap
