from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.generic.base import RedirectView
from django.conf import settings
from django.utils.translation import gettext as _
from django.contrib import messages
from apps.search.utils import paginate_results
from apps.search.tasks import perform_favorites_search
from apps.search.decorators import require_ajax
from celery.result import AsyncResult
import json
import six
from .tasks import create_favorites_results_file_xlsx, create_favorites_results_file_docx


class IndexView(TemplateView):
    template_name = 'favorites/index/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['favorites_ids'] = self.request.session.get('favorites_ids')

        # Recaptcha
        context['site_key'] = settings.RECAPTCHA_SITE_KEY
        context['RECAPTCHA_ENABLED'] = settings.RECAPTCHA_ENABLED

        if context['favorites_ids']:
            # Создание асинхронной задачи для Celery
            task = perform_favorites_search.delay(
                context['favorites_ids'],
                self.request.user.pk,
                dict(six.iterlists(self.request.GET))
            )
            context['task_id'] = task.id

        return context


@csrf_exempt
@require_POST
def add_or_remove(request):
    try:
        request.session['favorites_ids']
    except KeyError:
        request.session['favorites_ids'] = []

    if request.POST['id'] in request.session['favorites_ids']:
        request.session['favorites_ids'].remove(request.POST['id'])
    else:
        request.session['favorites_ids'].append(request.POST['id'])
    return JsonResponse({'success': True})


@require_ajax
def get_results_html(request):
    """Возвращает HTML с результатами простого поиска."""
    task_id = request.GET.get('task_id', None)
    if task_id is not None:
        task = AsyncResult(task_id)
        data = {}
        if task.state == 'SUCCESS':
            context = task.result
            data['state'] = task.state

            # Пагинация
            page = task.result['get_params']['page'][0] if task.result['get_params'].get('page') else 1
            results_on_page = task.result['get_params']['show'][0] if task.result['get_params'].get('show') else 10
            context['results'] = paginate_results(task.result['results'], page, results_on_page)

            # Формирование HTML с результатами
            data['result'] = render_to_string(
                f"favorites/index/_partials/results.html",
                context,
                request)
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('No job id given.')


class ClearRedirectView(RedirectView):
    """Очищает список избранного."""

    pattern_name = 'favorites:index'

    def get_redirect_url(self, *args, **kwargs):
        self.request.session['favorites_ids'] = []
        messages.success(
            self.request,
            _('Список вибраного успішно очищено.')
        )
        return super().get_redirect_url(*args, **kwargs)


def download_xls_favorites(request):
    """Возвращает JSON с id асинхронной задачи на формирование файла с результатами содержимого в избранном (xlsx)."""
    task = create_favorites_results_file_xlsx.delay(
        request.user.pk,
        request.session['favorites_ids'],
        dict(six.iterlists(request.GET)),
        'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    )
    return JsonResponse({'task_id': task.id})


def download_docx_favorites(request):
    """Возвращает JSON с id асинхронной задачи на формирование файла с результатами содержимого в избранном (docx)."""
    task = create_favorites_results_file_docx.delay(
        request.user.pk,
        request.session['favorites_ids'],
        dict(six.iterlists(request.GET)),
        'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    )
    return JsonResponse({'task_id': task.id})
