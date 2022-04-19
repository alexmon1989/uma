from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings
from .tasks import get_original_document
from .models import APIDescription


def original_document(request):
    """Отображает страницу с возможнлстью загрузки оригинального документа из Е=Архива."""
    if request.GET.get('sec_code'):
        task = get_original_document.delay(request.GET['sec_code'])
        return JsonResponse({'task_id': task.id})

    return render(
        request,
        'services/original_document/original_document.html',
        {'site_key': settings.RECAPTCHA_SITE_KEY, 'RECAPTCHA_ENABLED': settings.RECAPTCHA_ENABLED},
    )


def api_description(request):
    data, created = APIDescription.objects.get_or_create()
    lang = request.LANGUAGE_CODE
    return render(
        request,
        'services/api/index.html',
        {
            'title': getattr(data, f"title_{lang}"),
            'content': getattr(data, f"content_{lang}")
        }
    )
