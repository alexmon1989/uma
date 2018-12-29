from django.views.generic import TemplateView
from django.db.models import F
from django.forms import formset_factory, ValidationError
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404, HttpResponseServerError, FileResponse
from django.utils.http import urlencode
from django.shortcuts import redirect, reverse
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import ObjType, InidCodeSchedule, SimpleSearchField, AppDocuments, OrderService, OrderDocument
from .forms import AdvancedSearchForm, SimpleSearchForm
from .utils import (get_search_groups, elastic_search_groups, count_obj_types_filtered, count_obj_states_filtered,
                    get_client_ip, prepare_query, ResultsProxy)
from operator import attrgetter
from urllib.parse import parse_qs, urlparse
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A
from io import BytesIO
from zipfile import ZipFile
import time
import os


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
            try:
                is_valid = formset.is_valid()
            except ValidationError:
                raise Http404("Некоректний пошуковий запит.")

            # Признак того что производится поиск
            context['is_search'] = True

            if is_valid:
                # Формирование поискового запроса ElasticSearch
                client = Elasticsearch()
                qs = None
                for s in formset.cleaned_data:
                    elastic_field = SimpleSearchField.objects.get(pk=s['param_type']).elastic_index_field
                    if elastic_field:
                        q = Q(
                            'query_string',
                            query=prepare_query(s['value'], elastic_field.field_type),
                            default_field=elastic_field.field_name,
                            default_operator='AND'
                        )
                        if qs is not None:
                            qs &= q
                        else:
                            qs = q
                s = Search(using=client, index='uma').query(qs).sort('_score')

                # Агрегация для определения всех типов объектов и состояний
                s.aggs.bucket('idObjType_terms', A('terms', field='Document.idObjType'))
                s.aggs.bucket('obj_state_terms', A('terms', field='search_data.obj_state'))
                aggregations = s.execute().aggregations.to_dict()
                s_ = s

                # Фильтрация
                if self.request.GET.get('filter_obj_type'):
                    # Фильтрация в основном запросе
                    s = s.filter('terms', Document__idObjType=self.request.GET.getlist('filter_obj_type'))
                    # Агрегация для определения количества объектов определённых типов после применения одного фильтра
                    s_filter_obj_type = s_.filter(
                        'terms',
                        Document__idObjType=self.request.GET.getlist('filter_obj_type')
                    )
                    s_filter_obj_type.aggs.bucket('obj_state_terms', A('terms', field='search_data.obj_state'))
                    aggregations_obj_state = s_filter_obj_type.execute().aggregations.to_dict()
                    for bucket in aggregations['obj_state_terms']['buckets']:
                        if not list(filter(lambda x: x['key'] == bucket['key'], aggregations_obj_state['obj_state_terms']['buckets'])):
                            aggregations_obj_state['obj_state_terms']['buckets'].append(
                                {'key': bucket['key'], 'doc_count': 0}
                            )
                    aggregations['obj_state_terms']['buckets'] = aggregations_obj_state['obj_state_terms']['buckets']

                if self.request.GET.get('filter_obj_state'):
                    # Фильтрация в основном запросе
                    s = s.filter('terms', search_data__obj_state=self.request.GET.getlist('filter_obj_state'))
                    # Агрегация для определения количества объектов определённых состояний
                    # после применения одного фильтра
                    s_filter_obj_state = s_.filter(
                        'terms',
                        search_data__obj_state=self.request.GET.getlist('filter_obj_state')
                    )
                    s_filter_obj_state.aggs.bucket('idObjType_terms', A('terms', field='Document.idObjType'))
                    aggregations_id_obj_type = s_filter_obj_state.execute().aggregations.to_dict()
                    for bucket in aggregations['idObjType_terms']['buckets']:
                        if not list(filter(lambda x: x['key'] == bucket['key'], aggregations_id_obj_type['idObjType_terms']['buckets'])):
                            aggregations_id_obj_type['idObjType_terms']['buckets'].append(
                                {'key': bucket['key'], 'doc_count': 0}
                            )
                    aggregations['idObjType_terms']['buckets'] = aggregations_id_obj_type['idObjType_terms']['buckets']

                # Пагинация
                paginate_by = 10
                paginator = Paginator(ResultsProxy(s), paginate_by)
                page_number = self.request.GET.get('page')
                try:
                    page = paginator.page(page_number)
                except PageNotAnInteger:
                    page = paginator.page(1)
                except EmptyPage:
                    page = paginator.page(paginator.num_pages)

                context['results'] = page
                context['aggregations'] = aggregations
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
            try:
                is_valid = formset.is_valid()
            except ValidationError:
                raise Http404("Некоректний пошуковий запит.")

            # Признак того что производится поиск
            context['is_search'] = True

            # Поиск в ElasticSearch
            if is_valid:
                # Разбивка поисковых данных на поисковые группы
                search_groups = get_search_groups(formset.cleaned_data)

                # Поиск по каждой группе
                all_hits = elastic_search_groups(search_groups)

                # Сортировка результатов поиска (обратная сортировка по релевантности)
                all_hits = sorted(all_hits, key=attrgetter('meta.score'), reverse=True)

                # Типы объектов в найденных результатах
                obj_types = [{'id': x['obj_type'].id,
                              'title': getattr(x['obj_type'], f"obj_type_{context['lang_code']}")}
                             for x in search_groups]
                res_obj_types = list({v['id']: v for v in obj_types}.values())

                # Статусы в найденных результатах
                res_obj_states = []
                for i in range(1, 3):
                    count = len(list(filter(lambda x: x['search_data']['obj_state'] == i, all_hits)))
                    if count:
                        res_obj_states.append({'obj_state': i})

                # Фильтрация согласно фильтрам в сайдбаре
                context['results'] = all_hits
                if self.request.GET.get('filter_obj_type'):
                    context['results'] = list(
                        filter(lambda x: str(x['Document']['idObjType']) in self.request.GET.getlist('filter_obj_type'),
                               context['results']))
                if self.request.GET.get('filter_obj_state'):
                    context['results'] = list(
                        filter(lambda x: str(x['search_data']['obj_state']) in self.request.GET.getlist(
                            'filter_obj_state'),
                               context['results']))

                # Количество объектов определённых типов в отфильтрованных результатах
                context['res_obj_types'] = count_obj_types_filtered(
                    all_hits,
                    res_obj_types,
                    self.request.GET.getlist('filter_obj_state')
                )

                # Количество объектов определённых статусов в отфильтрованных результатах
                context['res_obj_states'] = count_obj_states_filtered(
                    all_hits,
                    res_obj_states,
                    self.request.GET.getlist('filter_obj_type')
                )

                # Пагинатор
                context['results_count'] = len(context['results'])
                paginator = Paginator(context['results'], 10)
                context['results'] = paginator.get_page(self.request.GET.get('page'))

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

    def get_context_data(self, **kwargs):
        """Передаёт доп. переменные в шаблон."""
        context = super().get_context_data(**kwargs)

        # Текущий язык приложения
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'

        # Поиск в ElasticSearch по номеру заявки, который является _id документа
        id_app_number = kwargs['id_app_number']
        client = Elasticsearch()
        s = Search().using(client).query("match", _id=id_app_number).execute()
        if not s:
            raise Http404("Об'єкт не знайдено")
        context['hit'], self.hit = s[0], s[0]
        context['biblio_data'] = self.hit.Claim if self.hit.search_data.obj_state == 1 else self.hit.Patent

        # Документы заявки (библиографические)
        context['biblio_documents'] = AppDocuments.get_app_documents(id_app_number)

        return context


@require_POST
def download_docs_zipped(request):
    """Инициирует загрузку архива с документами."""
    if request.POST.getlist('cead_id'):
        # Создание заказа
        order = OrderService(
            # user=request.user,
            user_id=3,
            ip_user=get_client_ip(request),
            app_id=request.POST['id_app_number']
        )
        order.save()
        for id_cead_doc in request.POST.getlist('cead_id'):
            OrderDocument.objects.create(order=order, id_cead_doc=id_cead_doc)

        # Проверка обработан ли заказ
        order_id = order.id
        completed = False
        counter = 0
        while completed is False:
            order = OrderService.objects.get(id=order_id)
            if order.order_completed:
                completed = True
            else:
                if counter == 5:
                    return HttpResponseServerError('Помилка сервісу видачі документів.')
                counter += 1
                time.sleep(3)

        # Создание архива
        in_memory = BytesIO()
        zip_ = ZipFile(in_memory, "a")
        for document in order.orderdocument_set.all():
            zip_.write(
                f"{settings.DOCUMENTS_MOUNT_FOLDER}/{order.user_id}/{order.id}/{document.id_cead_doc}.{document.file_type}",
                f"{document.id_cead_doc}.{document.file_type}"
            )

        # fix for Linux zip files read in Windows
        for file in zip_.filelist:
            file.create_system = 0

        zip_.close()
        in_memory.seek(0)
        return FileResponse(in_memory, as_attachment=True, filename='documents.zip')
    else:
        raise Http404('Файли не було обрано!')


def download_doc(request, id_app_number, id_cead_doc):
    """Инициирует у пользование скачивание документа."""
    # Создание заказа
    order = OrderService(
        # user=request.user,
        user_id=3,
        ip_user=get_client_ip(request),
        app_id=id_app_number
    )
    order.save()
    OrderDocument.objects.create(order=order, id_cead_doc=id_cead_doc)

    # Проверка обработан ли заказ
    order_id = order.id
    completed = False
    counter = 0
    while completed is False:
        order = OrderService.objects.get(id=order_id)
        if order.order_completed:
            completed = True
        else:
            if counter == 10:
                return HttpResponseServerError('Помилка сервісу видачі документів.')
            counter += 1
            time.sleep(2)

    # Получение документа из БД
    doc = order.orderdocument_set.first()
    if doc is None:
        raise Http404()

    # Путь к файлу
    file_path = os.path.join(
        settings.ORDERS_ROOT,
        str(order.user_id),
        str(order.id),
        f"{doc.id_cead_doc}.{doc.file_type}"
    )

    # Инициирование загрузки
    try:
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    except FileNotFoundError:
        raise Http404()
