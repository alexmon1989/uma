from django.middleware.locale import LocaleMiddleware
from django.conf import settings
from django.conf.urls.i18n import is_language_prefix_patterns_used
from django.utils import translation
from django.utils.translation.trans_real import (get_supported_language_variant, parse_accept_lang_header,
                                                 language_code_re)


def get_language_from_request(request, check_path=False):
    """
    Analyze the request to find what language the user wants the system to
    show. Only languages listed in settings.LANGUAGES are taken into account.
    If the user requests a sublanguage where we have a main language, we send
    out the main language.

    If check_path is True, the URL path prefix will be checked for a language
    code, otherwise this is skipped for backwards compatibility.
    """
    if check_path:
        lang_code = translation.get_language_from_path(request.path_info)
        if lang_code is not None:
            return lang_code

    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    try:
        return get_supported_language_variant(lang_code)
    except LookupError:
        pass

    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, unused in parse_accept_lang_header(accept):
        if accept_lang == '*':
            break

        # Если браузер настроен на русский язык, то считать украинский основным
        if accept_lang == 'ru':
            return settings.LANGUAGE_CODE

        if not language_code_re.search(accept_lang):
            continue

        try:
            return get_supported_language_variant(accept_lang)
        except LookupError:
            continue

    try:
        return get_supported_language_variant(settings.LANGUAGE_CODE)
    except LookupError:
        return settings.LANGUAGE_CODE


class MyLocaleMiddleware(LocaleMiddleware):
    """
    Переопределение LocaleMiddleware.
    Необходимо для того чтобы в случае, если браузер настроен на русский язык,
    показывался бы украинский интерфейс, а не английский.
    """
    def process_request(self, request):
        urlconf = getattr(request, 'urlconf', settings.ROOT_URLCONF)
        i18n_patterns_used, prefixed_default_language = is_language_prefix_patterns_used(urlconf)
        language = get_language_from_request(request, check_path=i18n_patterns_used)
        language_from_path = translation.get_language_from_path(request.path_info)
        if not language_from_path and i18n_patterns_used and not prefixed_default_language:
            language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        # Запомнить язык для текущей сессии
        request.session[translation.LANGUAGE_SESSION_KEY] = request.LANGUAGE_CODE
