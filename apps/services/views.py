import re
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from .models import APIDescription
from .tasks import get_original_document


@ensure_csrf_cookie
def original_document(request):
    """Отображает страницу с возможностью загрузки оригинального документа из Е-Архива."""
    return render(
        request,
        'services/original_document/original_document.html',
    )


@require_POST
def generate_original_document(request):
    """Запускает фоновую задачу формирования оригинального документа из Е-Архива."""
    sec_code = request.POST.get('sec_code', '').strip()
    if not re.fullmatch(r'^(?:cr)?\d{10}$', sec_code, re.IGNORECASE):
        return JsonResponse({'error': _('Довжина ідентифікатора документу невірна')}, status=400)

    task = get_original_document.delay(sec_code.upper())
    return JsonResponse({'task_id': task.id})


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
