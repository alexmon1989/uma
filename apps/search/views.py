from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.db.models import F, Q
from django.forms import formset_factory
from django.http import Http404, HttpResponse, JsonResponse
from django.utils.http import urlencode
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import user_passes_test
from django.template.loader import render_to_string
from django.conf import settings
from .models import (ObjType, InidCodeSchedule, SimpleSearchField, IpcAppList, SimpleSearchPage, AdvancedSearchPage,
                     AppVisit)
from .forms import AdvancedSearchForm, SimpleSearchForm
from .utils import (get_client_ip, paginate_results, get_ipc_codes_with_schedules)
from urllib.parse import parse_qs, urlparse
from celery.result import AsyncResult
import json
import six
import apps.search.tasks as tasks
from apps.search.decorators import check_recaptcha
from apps.bulletin.models import ClListOfficialBulletinsIp as Bulletin


class SimpleListView(TemplateView):
    """Отображает страницу с возможностью простого поиска."""
    template_name = 'search/simple/simple.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        lang_code = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'
        context['lang_code'] = lang_code

        # Данные страницы
        page_data, created = SimpleSearchPage.objects.get_or_create()
        context['page_description'] = getattr(page_data, f"description_{self.request.LANGUAGE_CODE}")

        # Recaptcha
        context['site_key'] = settings.RECAPTCHA_SITE_KEY
        context['RECAPTCHA_ENABLED'] = settings.RECAPTCHA_ENABLED

        # Параметры поиска
        context['search_parameter_types'] = list(SimpleSearchField.objects.annotate(
            field_label=F(f"field_label_{lang_code}")
        ).annotate(
            field_type=F('elastic_index_field__field_type')
        ).values(
            'id',
            'field_label',
            'field_type',
        ).filter(
            is_visible=True
        ).order_by(
            '-weight'
        ))

        context['show_search_form'] = True
        context['initial_data'] = {'form-TOTAL_FORMS': 1}
        SimpleSearchFormSet = formset_factory(SimpleSearchForm)
        if self.request.GET.get('form-TOTAL_FORMS'):
            formset = SimpleSearchFormSet(self.request.GET)
            context['initial_data'] = dict(formset.data.lists())

            # Признак того что производится поиск
            context['is_search'] = True

            # Показывать или скрывать поисковую форму
            context['show_search_form'] = self.request.session.get('show_search_form', False)

            # Количество результатов на странице
            self.request.session['show'] = self.request.GET.get(
                'show',
                self.request.session.get('show', 10)
            )
            get_params = dict(six.iterlists(self.request.GET))
            get_params['show'] = [self.request.session['show']]

            # Создание асинхронной задачи для Celery
            task = tasks.perform_simple_search.delay(
                self.request.user.pk,
                get_params
            )
            context['task_id'] = task.id

        return context


@check_recaptcha
def get_results_html(request):
    """Возвращает HTML с результатами простого поиска."""
    task_id = request.GET.get('task_id', None)
    search_type = request.GET.get('search_type', None)
    if task_id and task_id.strip() and search_type in ('simple', 'advanced', 'transactions'):
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
                results_on_page = task.result['get_params']['show'][0] if task.result['get_params'].get('show') else 10
                context['results'] = paginate_results(task.result['results'], page, results_on_page)

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

        # Данные страницы
        page_data, created = AdvancedSearchPage.objects.get_or_create()
        context['page_description'] = getattr(page_data, f"description_{self.request.LANGUAGE_CODE}")

        # Типы ОПС
        context['obj_types'] = list(
            ObjType.objects.order_by('order').annotate(
                value=F(f"obj_type_{context['lang_code']}")
            ).values('id', 'value')
        )

        # ИНИД-коды вместе с их реестрами
        context['ipc_codes'] = get_ipc_codes_with_schedules(context['lang_code'])

        # Recaptcha
        context['site_key'] = settings.RECAPTCHA_SITE_KEY

        context['show_search_form'] = True
        context['initial_data'] = {'form-TOTAL_FORMS': 1}
        AdvancedSearchFormSet = formset_factory(AdvancedSearchForm)
        if self.request.GET.get('form-TOTAL_FORMS'):
            formset = AdvancedSearchFormSet(self.request.GET)

            # Иниц. данные для формы
            context['initial_data'] = dict(formset.data.lists())

            # Признак того что производится поиск
            context['is_search'] = True

            # Показывать или скрывать поисковую форму
            context['show_search_form'] = self.request.session.get('show_search_form', False)

            # Количество результатов на странице
            self.request.session['show'] = self.request.GET.get(
                'show',
                self.request.session.get('show', 10)
            )
            get_params = dict(six.iterlists(self.request.GET))
            get_params['show'] = [self.request.session['show']]

            # Поиск в ElasticSearch
            # Создание асинхронной задачи для Celery
            task = tasks.perform_advanced_search.delay(
                self.request.user.pk,
                get_params
            )
            context['task_id'] = task.id

        context['RECAPTCHA_ENABLED'] = settings.RECAPTCHA_ENABLED

        return context


@require_POST
def add_filter_params(request):
    """Формирует строку параметров фильтра и делает переадресацию обратно на страницу поиска."""
    get_params = parse_qs(request.POST.get('get_params'))
    filters = ['filter_obj_type', 'filter_obj_state', 'filter_registration_status_color', 'filter_mark_status']
    for f in filters:
        get_params[f] = request.POST.getlist(f)
        if not get_params[f]:
            del get_params[f]

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
        task = tasks.get_app_details.delay(
            self.object.pk,
            self.request.user.pk
        )
        context['task_id'] = task.id

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Recaptcha
        context['RECAPTCHA_ENABLED'] = settings.RECAPTCHA_ENABLED
        context['site_key'] = settings.RECAPTCHA_SITE_KEY

        # Запись в лог запроса пользователя к заявке
        if not self.request.user.is_anonymous:
            AppVisit.objects.create(user=self.request.user, app=self.object)

        return context


@check_recaptcha
def get_data_app_html(request):
    """Возвращает HTML с данными по заявке после выполнения асинхронной задачи."""
    task_id = request.GET.get('task_id', None)
    if task_id and task_id.strip():
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
                    ipc_code__obj_types__id=context['hit']['Document']['idObjType']
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
                        Q(schedule_type__id__gte=3, schedule_type__id__lte=8) | Q(schedule_type__id__in=(16, 17, 18, 19, 30, 32, 34))
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
                elif context['hit']['Document']['idObjType'] in (9, 14):
                    if 'Code_441' in context['hit']['MadridTradeMark']['TradeMarkDetails']:
                        bul_num_441 = Bulletin.objects.get(
                            date_from__lte=context['hit']['MadridTradeMark']['TradeMarkDetails']['Code_441'],
                            date_to__gte=context['hit']['MadridTradeMark']['TradeMarkDetails']['Code_441']
                        )
                        context['code_441_bul_number'] = bul_num_441.bul_number
                    template = 'search/detail/tm_madrid/detail.html'
                elif context['hit']['Document']['idObjType'] in (10, 13):  # Авторське право
                    template = 'search/detail/copyright/detail.html'
                elif context['hit']['Document']['idObjType'] in (11, 12):  # Договора
                    template = 'search/detail/agreement/detail.html'
                elif context['hit']['Document']['idObjType'] == 16:
                    template = 'search/detail/inv_cert/detail.html'
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
def download_docs_zipped(request):
    """Инициирует загрузку архива с документами."""
    if request.POST.getlist('cead_id'):
        # Создание асинхронной задачи для получения архива с документами
        task = tasks.get_order_documents.delay(
            request.user.pk, request.POST['id_app_number'],
            request.POST.getlist('cead_id'),
            get_client_ip(request),
            request.LANGUAGE_CODE
        )
        return JsonResponse({'task_id': task.id})
    else:
        raise Http404('Файли не було обрано!')


def download_doc(request, id_app_number, id_cead_doc):
    """Возвращает JSON с id асинхронной задачи на заказ документа."""
    # Создание асинхронной задачи для получения документа
    task = tasks.get_order_documents.delay(
        request.user.pk, id_app_number, id_cead_doc, get_client_ip(request), request.LANGUAGE_CODE
    )
    return JsonResponse({'task_id': task.id})


@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Посадовці (чиновники)').exists())
def download_selection(request, id_app_number):
    """Возвращает JSON с id асинхронной задачи на формирование выписки."""
    task = tasks.create_selection.delay(id_app_number, request.user.pk, get_client_ip(request), request.GET)
    return JsonResponse({'task_id': task.id})


def validate_query(request):
    """Создаёт задание на валидацию запроса, который идёт в ElasticSearch (для валидации на стороне клиента)"""
    task = tasks.validate_query.delay(dict(six.iterlists(request.GET)))
    return HttpResponse(json.dumps({'task_id': task.id}), content_type='application/json')


def download_simple(request, format_: str):
    """Возвращает JSON с id асинхронной задачи на формирование файла с результатами простого поиска."""
    if format_ not in ('docx', 'xlsx'):
        raise Http404

    lang = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    get_params = dict(six.iterlists(request.GET))

    if format_ == 'docx':
        task = tasks.create_simple_search_results_file_docx.delay(
            request.user.pk,
            get_params,
            lang
        )
    else:  # xlsx
        task = tasks.create_simple_search_results_file_xlsx.delay(
            request.user.pk,
            get_params,
            lang
        )
    return JsonResponse({'task_id': task.id})


def download_advanced(request, format_: str):
    """Возвращает JSON с id асинхронной задачи на формирование файла с результатами расширенного поиска."""
    if format_ not in ('docx', 'xlsx'):
        raise Http404

    lang = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    get_params = dict(six.iterlists(request.GET))

    if format_ == 'docx':
        task = tasks.create_advanced_search_results_file_docx.delay(
            request.user.pk,
            get_params,
            lang
        )
    else:  # xlsx
        task = tasks.create_advanced_search_results_file_xlsx.delay(
            request.user.pk,
            get_params,
            lang
        )
    return JsonResponse({'task_id': task.id})


def download_details_docx(request, id_app_number: int):
    """Возвращает JSON с id асинхронной задачи на формирование файла
    с библиографическими данными объекта. пром. собств."""
    lang = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    task = tasks.create_details_file_docx.delay(
        id_app_number,
        request.user.pk,
        lang
    )
    return JsonResponse({'task_id': task.id})


def download_shared_docs(request, id_app_number):
    """Возвращает JSON с id асинхронной задачи на формирование архива с документами,
     которые доступны всем пользователям."""
    task = tasks.create_shared_docs_archive.delay(id_app_number)
    return JsonResponse({'task_id': task.id})


class TransactionsSearchView(TemplateView):
    """Отображает страницу с возможностью поиска по оповещениям."""
    template_name = 'search/transactions/index.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Recaptcha
        context['RECAPTCHA_ENABLED'] = settings.RECAPTCHA_ENABLED
        context['site_key'] = settings.RECAPTCHA_SITE_KEY

        context['initial_data'] = dict()
        context['is_search'] = False
        context['show_search_form'] = True
        if self.request.GET.get('obj_type') and self.request.GET.get('transaction_type') \
                and self.request.GET.get('date'):
            context['is_search'] = True

            # Показывать или скрывать поисковую форму
            context['show_search_form'] = self.request.session.get('show_search_form', False)

            # Количество результатов на странице
            self.request.session['show'] = self.request.GET.get(
                'show',
                self.request.session.get('show', 10)
            )
            get_params = dict(six.iterlists(self.request.GET))
            get_params['show'] = [self.request.session['show']]

            context['initial_data'] = dict(six.iterlists(self.request.GET))

            # Поиск
            # Создание асинхронной задачи для Celery
            task = tasks.perform_transactions_search.delay(
                get_params
            )
            context['task_id'] = task.id

        return context


def download_transactions(request, format_: str):
    """Возвращает JSON с id асинхронной задачи на формирование файла с результатами поиска по оповещениям."""
    if format_ not in ('docx', 'xlsx'):
        raise Http404

    lang = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    get_params = dict(six.iterlists(request.GET))

    if format_ == 'docx':
        task = tasks.create_transactions_search_results_file_docx.delay(
            get_params,
            lang
        )
    else:  # xlsx
        task = tasks.create_transactions_search_results_file_xlsx.delay(
            get_params,
            lang
        )
    return JsonResponse({'task_id': task.id})


@check_recaptcha
def get_task_info(request):
    """Возвращает JSON с результатами выполнения асинхронного задания."""
    task_id = request.GET.get('task_id', None)
    if task_id and task_id.strip():
        task = AsyncResult(task_id)
        data = {
            'state': task.state,
            'result': task.result,
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponse('No job id given.')


def get_validation_info(request):
    """Возвращает JSON с результатами валидации поискового запроса."""
    task_id = request.GET.get('task_id', None)
    if task_id and task_id.strip():
        task = AsyncResult(task_id)
        data = {
            'state': task.state,
            'result': bool(task.result),
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    else:
        return HttpResponse('No job id given.')


def get_obj_types_with_transactions(request):
    """Создаёт задачу на получение типов объектов их типами оповещений."""
    lang_code = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'
    task = tasks.get_obj_types_with_transactions.delay(lang_code)
    return HttpResponse(json.dumps({'task_id': task.id}), content_type='application/json')


@require_POST
@csrf_exempt
def toggle_search_form(request):
    """Записывает в сессию значение того нужно ли держать форму открытой постоянно."""
    request.session['show_search_form'] = not request.session.get('show_search_form', False)
    return JsonResponse({'visible': request.session.get('show_search_form')})
