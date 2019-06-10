from django.views.generic import TemplateView
from django.db.models import F
from django.forms import formset_factory
from django.http import Http404, HttpResponseServerError, FileResponse, JsonResponse, HttpResponse
from django.utils import six
from django.utils.http import urlencode
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.conf import settings
from django.contrib.admin.views.decorators import user_passes_test
from django.core.exceptions import SuspiciousOperation
from .models import ObjType, InidCodeSchedule, SimpleSearchField, AppDocuments, OrderService, OrderDocument, IpcAppList
from .forms import AdvancedSearchForm, SimpleSearchForm, TransactionsSearchForm
from .utils import (get_search_groups, get_elastic_results, get_client_ip, prepare_simple_query, paginate_results,
                    filter_results, extend_doc_flow, get_completed_order, create_selection_inv_um_ld,
                    get_data_for_selection_tm, create_selection_tm, filter_bad_apps, sort_results,
                    user_has_access_to_docs_decorator, create_search_res_doc, prepare_data_for_search_report,
                    get_transactions_types, get_search_in_transactions, filter_unpublished_apps)
from urllib.parse import parse_qs, urlparse
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from zipfile import ZipFile
from pathlib import Path
import os, io, json


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

            # Валидация поисковой формы
            is_valid = formset.is_valid()
            if not is_valid:
                context['formset_errors'] = formset.errors

            # Признак того что производится поиск
            context['is_search'] = True

            if is_valid:
                # Формирование поискового запроса ElasticSearch
                client = Elasticsearch(settings.ELASTIC_HOST)
                qs = None
                for s in formset.cleaned_data:
                    elastic_field = SimpleSearchField.objects.get(pk=s['param_type']).elastic_index_field
                    if elastic_field:
                        q = Q(
                            'query_string',
                            query=prepare_simple_query(s['value'], elastic_field.field_type),
                            default_field=elastic_field.field_name,
                            default_operator='AND'
                        )
                        if qs is not None:
                            qs &= q
                        else:
                            qs = q

                if qs is not None:
                    # Не показывать заявки, по которым выдан охранный документ
                    qs = filter_bad_apps(qs)

                    # Не показывать неопубликованные заявки
                    qs = filter_unpublished_apps(self.request.user, qs)

                s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(qs)

                # Сортировка
                if self.request.GET.get('sort_by'):
                    s = sort_results(s, self.request.GET['sort_by'])
                else:
                    s = s.sort('_score')

                # Фильтрация, агрегация
                s, context['aggregations'] = filter_results(s, self.request)

                # Пагинация
                context['results'] = paginate_results(s, self.request.GET.get('page'), 10)

        return context


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

            # Валидация поисковой формы
            is_valid = formset.is_valid()
            if not is_valid:
                context['formset_errors'] = formset.errors

            # Признак того что производится поиск
            context['is_search'] = True

            # Поиск в ElasticSearch
            if is_valid:
                # Разбивка поисковых данных на поисковые группы
                search_groups = get_search_groups(formset.cleaned_data)

                # Поиск в ElasticSearch по каждой группе
                s = get_elastic_results(search_groups, self.request.user)

                # Сортировка
                if self.request.GET.get('sort_by'):
                    s = sort_results(s, self.request.GET['sort_by'])
                else:
                    s = s.sort('_score')

                # Фильтрация, агрегация
                s, context['aggregations'] = filter_results(s, self.request)

                # Пагинация
                context['results'] = paginate_results(s, self.request.GET.get('page'), 10)

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


class ObjectDetailView(TemplateView):
    """Отображает страницу с детальной информацией по объекту"""
    hit = None

    def get_template_names(self):
        if self.hit['Document']['idObjType'] in (1, 2):
            return ['search/detail/inv_um/detail.html']
        elif self.hit['Document']['idObjType'] == 3:
            return ['search/detail/ld/detail.html']
        elif self.hit['Document']['idObjType'] == 4:
            return ['search/detail/tm/detail.html']
        elif self.hit['Document']['idObjType'] == 6:
            return ['search/detail/id/detail.html']

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Поиск в ElasticSearch по номеру заявки, который является _id документа
        id_app_number = kwargs['id_app_number']
        client = Elasticsearch(settings.ELASTIC_HOST)
        q = Q(
            'bool',
            must=[Q('match', _id=id_app_number)],
        )
        q = filter_bad_apps(q) # Исключение заявок, не пригодных к отображению
        q = filter_unpublished_apps(self.request.user, q)
        s = Search().using(client).query(q).execute()
        if not s:
            raise Http404("Об'єкт не знайдено")
        context['hit'], self.hit = s[0], s[0]

        if self.hit['Document']['idObjType'] in (1, 2, 3):
            context['biblio_data'] = self.hit.Claim if self.hit.search_data.obj_state == 1 else self.hit.Patent

            # Оповещения
            context['transactions'] = self.hit.to_dict().get('TRANSACTIONS', {}).get('TRANSACTION', [])
            if type(context['transactions']) is dict:
                context['transactions'] = [context['transactions']]
            # Документы заявки (библиографические)
            context['biblio_documents'] = AppDocuments.get_app_documents(id_app_number)

            # Если это патент, то необходимо объеденить документы, платежи и т.д. с теми которые были на этапе заявки
            if self.hit.search_data.obj_state == 2:
                extend_doc_flow(context['hit'])

        # Видимость полей библиографических данных
        ipc_fields = InidCodeSchedule.objects.filter(
            ipc_code__obj_type__id=self.hit.Document.idObjType
        ).annotate(
            code_title=F(f"ipc_code__code_value_{context['lang_code']}"),
            ipc_code_short=F('ipc_code__code_inid')
        ).values('ipc_code_short', 'code_title', 'enable_view')
        if self.hit['search_data']['obj_state'] == 1:
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

        context['id_app_number'] = id_app_number
        return context


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

        # Проверка обработан ли заказ
        order_id = order.id
        order = get_completed_order(order_id)
        if order:
            # Создание архива
            in_memory = io.BytesIO()
            zip_ = ZipFile(in_memory, "a")
            for document in order.orderdocument_set.all():
                zip_.write(
                    f"{settings.DOCUMENTS_MOUNT_FOLDER}/OrderService/{order.user_id}/{order.id}/{document.file_name}",
                    f"{document.file_name}"
                )

            # fix for Linux zip files read in Windows
            for file in zip_.filelist:
                file.create_system = 0

            zip_.close()
            in_memory.seek(0)
            return FileResponse(in_memory, as_attachment=True, filename='documents.zip')
        else:
            return HttpResponseServerError('Помилка сервісу видачі документів.')
    else:
        raise Http404('Файли не було обрано!')


@user_has_access_to_docs_decorator
def download_doc(request, id_app_number, id_cead_doc):
    """Инициирует у пользование скачивание документа."""
    # Создание заказа
    order = OrderService(
        # user=request.user,
        user_id=request.user.pk,
        ip_user=get_client_ip(request),
        app_id=id_app_number
    )
    order.save()
    OrderDocument.objects.create(order=order, id_cead_doc=id_cead_doc)

    # Проверка обработан ли заказ
    order_id = order.id
    order = get_completed_order(order_id)
    if order:
        # Получение документа из БД
        doc = order.orderdocument_set.first()
        if doc is None:
            raise Http404()

        # Путь к файлу
        file_path = os.path.join(
            settings.ORDERS_ROOT,
            str(order.user_id),
            str(order.id),
            doc.file_name
        )

        # Инициирование загрузки
        try:
            return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        except FileNotFoundError:
            raise Http404()
    else:
        return HttpResponseServerError('Помилка сервісу видачі документів.')


@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Посадовці (чиновники)').exists())
def download_selection_inv_um_ld(request, id_app_number):
    """Инициирует загрузку выписки по охранному документу для изобретений, полезных моделей, топографий."""
    app = get_object_or_404(IpcAppList, id=id_app_number, registration_number__gt=0, obj_type_id__in=(1, 2, 3))

    # Создание заказа
    order = OrderService(
        # user=request.user,
        user_id=request.user.pk,
        ip_user=get_client_ip(request),
        app_id=id_app_number,
        create_external_documents=1,
        externaldoc_enternum=270,
        order_completed=False
    )
    order.save()

    # Проверка обработан ли заказ
    order_id = order.id
    order = get_completed_order(order_id)
    if order:
        # Формирование выписки
        file_stream = create_selection_inv_um_ld(json.loads(order.external_doc_body), request.GET)

        return FileResponse(
            file_stream,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            filename=f"{app.registration_number}.docx"
        )
    else:
        return HttpResponseServerError('Помилка сервісу видачі документів.')


@user_passes_test(lambda u: u.is_superuser or u.groups.filter(name='Посадовці (чиновники)').exists())
def download_selection_tm(request, id_app_number):
    """Инициирует загрузку выписки по охранному документу для знаков для товаров и услуг."""
    # Формирование поискового запроса ElasticSearch
    client = Elasticsearch(settings.ELASTIC_HOST)
    q = Q(
        'bool',
        must=[
            Q('match', _id=id_app_number),
            Q('match', Document__Status=3),
            Q('match', search_data__obj_state=2),
            Q('match', Document__idObjType=4),
        ],
    )
    s = Search().using(client).query(q).execute()
    if s:
        hit = s[0]
        data = get_data_for_selection_tm(hit)
        file_stream = create_selection_tm(data, request.GET)

        return FileResponse(
            file_stream,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            filename=f"{hit.search_data.protective_doc_number}.docx"
        )
    else:
        raise Http404("Об'єкт не знайдено")


def validate_query(request):
    """Проводит валидацию запроса, который идёт в ElasticSearch (для валидации на стороне клиента)"""
    search_type = request.GET.get('search_type')
    if search_type == 'simple':
        form = SimpleSearchForm(request.GET)
    elif search_type == 'advanced':
        form = AdvancedSearchForm(request.GET)
    else:
        raise SuspiciousOperation("Невірні параметри.")

    return JsonResponse({'result': int(form.is_valid())})


def download_xls_simple(request):
    """Формирует CSV-файл с результатами простого поиска и инициирует его загрузку у пользователя."""
    SimpleSearchFormSet = formset_factory(SimpleSearchForm)
    formset = SimpleSearchFormSet(request.GET)
    if formset.is_valid:
        # Формирование поискового запроса ElasticSearch
        client = Elasticsearch(settings.ELASTIC_HOST)
        qs = None
        for s in formset.cleaned_data:
            elastic_field = SimpleSearchField.objects.get(pk=s['param_type']).elastic_index_field
            if elastic_field:
                q = Q(
                    'query_string',
                    query=prepare_simple_query(s['value'], elastic_field.field_type),
                    default_field=elastic_field.field_name,
                    default_operator='AND'
                )
                if qs is not None:
                    qs &= q
                else:
                    qs = q

        if qs is not None:
            # Не показывать заявки, по которым выдан охранный документ
            qs = filter_bad_apps(qs)
            # Не показывать неопубликованные заявки
            qs = filter_unpublished_apps(request.user, qs)

        s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(qs)

        # Фильтрация
        if request.GET.get('filter_obj_type'):
            # Фильтрация по типу объекта
            s = s.filter('terms', Document__idObjType=request.GET.getlist('filter_obj_type'))

        if request.GET.get('filter_obj_state'):
            # Фильтрация по статусу объекта
            s = s.filter('terms', search_data__obj_state=request.GET.getlist('filter_obj_state'))

        if s.count() <= 5000:

            s = s.source(['search_data', 'Document'])

            # Сортировка
            if request.GET.get('sort_by'):
                s = sort_results(s, request.GET['sort_by'])
            else:
                s = s.sort('_score')

            # Текущий язык
            lang_code = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'

            # Данные для Excel-файла
            data = prepare_data_for_search_report(s, lang_code)

            # Формировние Excel-файла
            workbook = create_search_res_doc(data)

            # Отправка в браузер
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=search_results.xls'
            workbook.save(response)
            return response

    raise Http404


def download_xls_advanced(request):
    """Формирует CSV-файл с результатами расширенного поиска и инициирует его загрузку у пользователя."""
    AdvancedSearchFormSet = formset_factory(AdvancedSearchForm)
    if request.GET:
        formset = AdvancedSearchFormSet(request.GET)

        # Поиск в ElasticSearch
        if formset.is_valid():
            # Разбивка поисковых данных на поисковые группы
            search_groups = get_search_groups(formset.cleaned_data)

            # Поиск в ElasticSearch по каждой группе
            s = get_elastic_results(search_groups)

            # Фильтрация
            if request.GET.get('filter_obj_type'):
                # Фильтрация по типу объекта
                s = s.filter('terms', Document__idObjType=request.GET.getlist('filter_obj_type'))
            if request.GET.get('filter_obj_state'):
                # Фильтрация по статусу объекта
                s = s.filter('terms', search_data__obj_state=request.GET.getlist('filter_obj_state'))

            if s.count() <= 5000:
                s = s.source(['search_data', 'Document'])

                # Сортировка
                if request.GET.get('sort_by'):
                    s = sort_results(s, request.GET['sort_by'])
                else:
                    s = s.sort('_score')

                # Текущий язык
                lang_code = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'

                # Данные для Excel-файла
                data = prepare_data_for_search_report(s, lang_code)

                # Формировние Excel-файла
                workbook = create_search_res_doc(data)

                # Отправка в браузер
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=search_results.xls'
                workbook.save(response)
                return response

    raise Http404


def download_shared_docs(request, id_app_number):
    """Инициирует загрузку у пользователя документов, которые доступны всем пользователям"""
    app = get_object_or_404(IpcAppList, id=id_app_number, registration_number__gt=0, obj_type_id__in=(1, 2, 3))

    # Создание архива
    in_memory = io.BytesIO()
    zip_ = ZipFile(in_memory, "a")
    for document in app.appdocuments_set.all():
        zip_.write(
            document.file_name.replace('\\\\bear\\share\\', settings.DOCUMENTS_MOUNT_FOLDER).replace('\\', '/'),
            Path(document.file_name.replace('\\', '/')).name
        )

    # fix for Linux zip files read in Windows
    for file in zip_.filelist:
        file.create_system = 0

    zip_.close()
    in_memory.seek(0)
    return FileResponse(in_memory, as_attachment=True, filename='documents.zip')


class TransactionsSearchView(TemplateView):
    """Отображает страницу с возможностью поиска по оповещениям."""
    template_name = 'search/transactions/index.html'

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Типы ОПС
        context['obj_types'] = list(
            ObjType.objects.order_by('id').annotate(value=F(f"obj_type_{context['lang_code']}")).values('id', 'value')
        )

        # Типы оповещений
        for obj_type in context['obj_types']:
            obj_type['transactions_types'] = get_transactions_types(obj_type['id'])

        context['initial_data'] = dict()
        context['is_search'] = False
        if self.request.GET:
            form = TransactionsSearchForm(self.request.GET)
            is_valid = form.is_valid()
            context['is_search'] = True
            context['form'] = form
            context['initial_data'] = dict(six.iterlists(self.request.GET))

            # Поиск
            if is_valid:
                s = get_search_in_transactions(form.cleaned_data)
                if s:
                    # Сортировка
                    if self.request.GET.get('sort_by'):
                        s = sort_results(s, self.request.GET['sort_by'])
                    else:
                        s = s.sort('_score')

                    # Пагинация
                    context['results'] = paginate_results(s, self.request.GET.get('page'), 10)

        return context


def download_xls_transactions(request):
    """Формирует CSV-файл с результатами поиска по транзакциям."""
    form = TransactionsSearchForm(request.GET)
    if form.is_valid():

        s = get_search_in_transactions(form.cleaned_data)
        if s:
            # Сортировка
            if request.GET.get('sort_by'):
                s = sort_results(s, request.GET['sort_by'])
            else:
                s = s.sort('_score')

            if s.count() <= 5000:
                s = s.source(['search_data', 'Document'])

                # Сортировка
                if request.GET.get('sort_by'):
                    s = sort_results(s, request.GET['sort_by'])
                else:
                    s = s.sort('_score')

                # Текущий язык
                lang_code = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'

                # Данные для Excel-файла
                data = prepare_data_for_search_report(s, lang_code)

                # Формировние Excel-файла
                workbook = create_search_res_doc(data)

                # Отправка в браузер
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=search_results.xls'
                workbook.save(response)
                return response

    raise Http404
