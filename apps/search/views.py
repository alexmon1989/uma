from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.db.models import F
from django.forms import formset_factory
from django.http import Http404, HttpResponse, JsonResponse
from django.utils import six
from django.utils.http import urlencode
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import user_passes_test
from django.template.loader import render_to_string
from .models import ObjType, InidCodeSchedule, SimpleSearchField, OrderService, OrderDocument, IpcAppList
from .forms import AdvancedSearchForm, SimpleSearchForm, TransactionsSearchForm
from .utils import (get_client_ip, paginate_results, user_has_access_to_docs_decorator)
from urllib.parse import parse_qs, urlparse
from celery.result import AsyncResult
import json
from .tasks import (perform_simple_search, validate_query as validate_query_task, get_app_details,
                    perform_advanced_search, perform_transactions_search,
                    get_obj_types_with_transactions as get_obj_types_with_transactions_task, get_order_documents,
                    create_selection, create_simple_search_results_file, create_advanced_search_results_file,
                    create_transactions_search_results_file, create_shared_docs_archive)


class SimpleListView(TemplateView):
    """Отображает страницу с возможностью простого поиска."""
    template_name = 'search/simple/simple.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        lang_code = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'
        context['lang_code'] = lang_code

        # Параметры поиска
        context['search_parameter_types'] = list(SimpleSearchField.objects.annotate(
            field_label=F(f"field_label_{lang_code}")
        ).values(
            'id',
            'field_label',
        ).filter(is_visible=True).order_by('-weight'))

        context['initial_data'] = {'form-TOTAL_FORMS': 1}
        SimpleSearchFormSet = formset_factory(SimpleSearchForm)
        if self.request.GET:
            formset = SimpleSearchFormSet(self.request.GET)
            context['initial_data'] = dict(formset.data.lists())

            # Признак того что производится поиск
            context['is_search'] = True

            # Создание асинхронной задачи для Celery
            task = perform_simple_search.delay(
                self.request.user.pk,
                dict(six.iterlists(self.request.GET))
            )
            context['task_id'] = task.id

        return context


def get_results_html(request):
    """Возвращает HTML с результатами простого поиска."""
    task_id = request.GET.get('task_id', None)
    search_type = request.GET.get('search_type', None)
    if task_id is not None and search_type in ('simple', 'advanced', 'transactions'):
        task = AsyncResult(task_id)
        data = {}
        if task.state == 'SUCCESS':
            context = task.result
            context['lang_code'] = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
            data['state'] = 'SUCCESS'

            if task.result.get('validation_errors'):
                context['validation_errors'] = task.result['validation_errors']
            else:
                # Пагинация
                page = task.result['get_params']['page'][0] if task.result['get_params'].get('page') else 1
                context['results'] = paginate_results(task.result['results'], page, 10)

            # Формирование HTML с результатами
            data['result'] = render_to_string(
                f"search/{search_type}/_partials/results.html",
                context,
                request)
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('No job id given.')


class AdvancedListView(TemplateView):
    """Отображает страницу с возможностью расширенного поиска."""
    template_name = 'search/advanced/advanced.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Типы ОПС
        context['obj_types'] = list(
            ObjType.objects.order_by('id').annotate(value=F(f"obj_type_{context['lang_code']}")).values('id', 'value')
        )

        # ИНИД-коды вместе с их реестрами
        context['ipc_codes'] = InidCodeSchedule.get_ipc_codes_with_schedules(context['lang_code'])

        context['initial_data'] = {'form-TOTAL_FORMS': 1}
        AdvancedSearchFormSet = formset_factory(AdvancedSearchForm)
        if self.request.GET:
            formset = AdvancedSearchFormSet(self.request.GET)

            # Иниц. данные для формы
            context['initial_data'] = dict(formset.data.lists())

            # Признак того что производится поиск
            context['is_search'] = True

            # Поиск в ElasticSearch
            # Создание асинхронной задачи для Celery
            task = perform_advanced_search.delay(
                self.request.user.pk,
                dict(six.iterlists(self.request.GET))
            )
            context['task_id'] = task.id

        return context


@require_POST
def add_filter_params(request):
    """Формирует строку параметров фильтра и делает переадресацию обратно на страницу поиска."""
    get_params = parse_qs(request.POST.get('get_params'))
    get_params['filter_obj_type'] = request.POST.getlist('filter_obj_type')
    get_params['filter_obj_state'] = request.POST.getlist('filter_obj_state')

    if not get_params['filter_obj_type']:
        del get_params['filter_obj_type']

    if not get_params['filter_obj_state']:
        del get_params['filter_obj_state']

    if get_params.get('page'):
        del get_params['page']  # Для переадресации на 1 страницу

    get_params = urlencode(get_params, True)

    referer = request.META.get('HTTP_REFERER')
    path = urlparse(referer).path

    return redirect(f"{path}?{get_params}")


class ObjectDetailView(DetailView):
    """Отображает страницу с детальной информацией по объекту"""
    model = IpcAppList
    template_name = 'search/detail/detail.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Создание асинхронной задачи на получение данных объекта
        task = get_app_details.delay(
            self.object.pk,
            self.request.user.pk
        )
        context['task_id'] = task.id

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        return context


def get_data_app_html(request):
    """Возвращает HTML с данными по заявке после выполнения асинхронной задачи."""
    task_id = request.GET.get('task_id', None)
    if task_id is not None:
        task = AsyncResult(task_id)
        data = {}
        if task.state == 'SUCCESS':
            context = dict()
            data['state'] = 'SUCCESS'
            if task.result:
                context['hit'] = task.result
                context['lang_code'] = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'

                # Видимость полей библиографических данных
                ipc_fields = InidCodeSchedule.objects.filter(
                    ipc_code__obj_type__id=context['hit']['Document']['idObjType']
                ).annotate(
                    code_title=F(f"ipc_code__code_value_{context['lang_code']}"),
                    ipc_code_short=F('ipc_code__code_inid')
                ).values('ipc_code_short', 'code_title', 'enable_view')
                if context['hit']['search_data']['obj_state'] == 1:
                    ipc_fields = ipc_fields.filter(
                        schedule_type__id__gte=9,
                        schedule_type__id__lte=15,
                    )
                else:
                    ipc_fields = ipc_fields.filter(
                        schedule_type__id__gte=3,
                        schedule_type__id__lte=8,
                    )
                context['ipc_fields'] = ipc_fields

                # Путь к шаблону в зависимости от типа объекта
                if context['hit']['Document']['idObjType'] in (1, 2):
                    template = 'search/detail/inv_um/detail.html'
                elif context['hit']['Document']['idObjType'] == 3:
                    template = 'search/detail/ld/detail.html'
                elif context['hit']['Document']['idObjType'] == 4:
                    template = 'search/detail/tm/detail.html'
                elif context['hit']['Document']['idObjType'] == 5:
                    template = 'search/detail/qi/detail.html'
                elif context['hit']['Document']['idObjType'] == 6:
                    template = 'search/detail/id/detail.html'
                else:
                    template = 'search/detail/not_found.html'
            else:
                template = 'search/detail/not_found.html'

            # Формирование HTML с результатами
            data['result'] = render_to_string(
                template,
                context,
                request
            )
        return HttpResponse(json.dumps(data), content_type='application/json')
    return HttpResponse('No job id given.')


@require_POST
@user_has_access_to_docs_decorator
def download_docs_zipped(request):
    """Инициирует загрузку архива с документами."""
    if request.POST.getlist('cead_id'):
        # Создание заказа
        order = OrderService(
            # user=request.user,
            user_id=request.user.pk,
            ip_user=get_client_ip(request),
            app_id=request.POST['id_app_number']
        )
        order.save()
        for id_cead_doc in request.POST.getlist('cead_id'):
            OrderDocument.objects.create(order=order, id_cead_doc=id_cead_doc)

        # Создание асинхронной задачи для получения архива с документами
        task = get_order_documents.delay(order.id)
        return JsonResponse({'task_id': task.id})
    else:
        raise Http404('Файли не було обрано!')


@user_has_access_to_docs_decorator
def download_doc(request, id_app_number, id_cead_doc):
    """Возвращает JSON с id асинхронной задачи на заказ документа."""
    # Создание заказа
    order = OrderService(
        # user=request.user,
        user_id=request.user.pk,
        ip_user=get_client_ip(request),
        app_id=id_app_number
    )
    order.save()
    OrderDocument.objects.create(order=order, id_cead_doc=id_cead_doc)

    # Создание асинхронной задачи для получения документа
    task = get_order_documents.delay(order.id)
    return JsonResponse({'task_id': task.id})


@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Посадовці (чиновники)').exists())
def download_selection(request, id_app_number):
    """Возвращает JSON с id асинхронной задачи на формирование выписки."""
    task = create_selection.delay(id_app_number, request.user.pk, get_client_ip(request), request.GET)
    return JsonResponse({'task_id': task.id})


def validate_query(request):
    """Создаёт задание на валидацию запроса, который идёт в ElasticSearch (для валидации на стороне клиента)"""
    task = validate_query_task.delay(dict(six.iterlists(request.GET)))
    return HttpResponse(json.dumps({'task_id': task.id}), content_type='application/json')


def download_xls_simple(request):
    """Возвращает JSON с id асинхронной задачи на формирование файла с результатами простого поиска."""
    task = create_simple_search_results_file.delay(
        request.user.pk,
        dict(six.iterlists(request.GET)),
        'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    )
    return JsonResponse({'task_id': task.id})


def download_xls_advanced(request):
    """Возвращает JSON с id асинхронной задачи на формирование файла с результатами расширенного поиска."""
    task = create_advanced_search_results_file.delay(
        request.user.pk,
        dict(six.iterlists(request.GET)),
        'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    )
    return JsonResponse({'task_id': task.id})


def download_shared_docs(request, id_app_number):
    """Возвращает JSON с id асинхронной задачи на формирование архива с документами,
     которые доступны всем пользователям."""
    task = create_shared_docs_archive.delay(id_app_number)
    return JsonResponse({'task_id': task.id})


class TransactionsSearchView(TemplateView):
    """Отображает страницу с возможностью поиска по оповещениям."""
    template_name = 'search/transactions/index.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        context['initial_data'] = dict()
        context['is_search'] = False
        if self.request.GET:
            context['is_search'] = True
            context['initial_data'] = dict(six.iterlists(self.request.GET))

            # Поиск
            # Создание асинхронной задачи для Celery
            task = perform_transactions_search.delay(
                dict(six.iterlists(self.request.GET))
            )
            context['task_id'] = task.id

        return context


def download_xls_transactions(request):
    """Возвращает JSON с id асинхронной задачи на формирование файла с результатами поиска по оповещениям."""
    task = create_transactions_search_results_file.delay(
        dict(six.iterlists(request.GET)),
        'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    )
    return JsonResponse({'task_id': task.id})


def get_task_info(request):
    """Возвращает JSON с результатами выполнения асинхронного задания."""
    task_id = request.GET.get('task_id', None)
    if task_id is not None:
        task = AsyncResult(task_id)
        data = {
            'state': task.state,
            'result': task.result,
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponse('No job id given.')


def get_obj_types_with_transactions(request):
    """Создаёт задачу на получение типов объектов их типами оповещений."""
    lang_code = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    task = get_obj_types_with_transactions_task.delay(lang_code)
    return HttpResponse(json.dumps({'task_id': task.id}), content_type='application/json')
