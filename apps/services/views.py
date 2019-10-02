from django.http import JsonResponse
from django.shortcuts import render
from .tasks import get_original_document


def original_document(request):
    """Отображает страницу с возможнлстью загрузки оригинального документа из Е=Архива."""
    if request.GET.get('sec_code'):
        task = get_original_document.delay(request.GET['sec_code'])
        return JsonResponse({'task_id': task.id})

    return render(request, 'services/original_document/original_document.html')
