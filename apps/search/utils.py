from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A
from .models import ObjType, InidCodeSchedule, OrderService
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.shared import Pt, Cm
import re
import time
import datetime
import io


def get_search_groups(search_data):
    """Разбивка поисковых данных на поисковые группы"""
    search_groups = []
    for obj_type in ObjType.objects.all():
        # Поисковые запросы на заявки
        search_groups.append({
            'obj_type': obj_type,
            'obj_state': 1,
            'search_params': list(filter(
                lambda x: x['obj_type'] == obj_type.pk and '1' in x['obj_state'],
                search_data
            ))
        })
        # Поисковые запросы на охранные документы
        search_groups.append({
            'obj_type': obj_type,
            'obj_state': 2,
            'search_params': list(filter(
                lambda x: x['obj_type'] == obj_type.pk and '2' in x['obj_state'],
                search_data
            ))
        })
    # Фильтрация пустых групп
    search_groups = filter(lambda x: len(x['search_params']) > 0, search_groups)
    return list(search_groups)


def prepare_advanced_query(query, field_type):
    """Обрабатывает строку расширенного запроса пользователя."""
    if field_type == 'date':
        # Форматирование дат
        query = re.sub(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '\\3-\\2-\\1', query)
    query = query.replace(" ТА ", " AND ").replace(" АБО ", " OR ").replace(" НЕ ", " NOT ")
    return query


def prepare_simple_query(query, field_type):
    """Обрабатывает строку простого запроса пользователя."""
    if field_type == 'date':
        # Форматирование дат
        query = re.sub(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '\\3-\\2-\\1', query)
    return query


def get_elastic_results(search_groups):
    """Поиск в ElasticSearch по группам."""
    qs_list = []
    for group in search_groups:
        if group['search_params']:
            # Идентификаторы schedule_type для заявок или охранных документов
            schedule_type_ids = (10, 11, 12, 13, 14, 15) if group['obj_state'] == 1 else (3, 4, 5, 6, 7, 8)
            qs = None

            for search_param in group['search_params']:
                # Поле поиска ElasticSearch
                inid_schedule = InidCodeSchedule.objects.filter(
                    ipc_code__id=search_param['ipc_code'],
                    schedule_type__obj_type=group['obj_type'],
                    schedule_type__id__in=schedule_type_ids
                ).first()

                # Проверка доступно ли поле для поиска
                if inid_schedule.enable_search and inid_schedule.elastic_index_field is not None:
                    q = Q(
                        'query_string',
                        query=f"{prepare_advanced_query(search_param['value'], inid_schedule.elastic_index_field.field_type)}",
                        default_field=inid_schedule.elastic_index_field.field_name,
                        analyze_wildcard=True
                    )
                    if not qs:
                        qs = q
                    else:
                        qs &= q

            if qs is not None:
                qs &= Q('query_string', query=f"{group['obj_type'].pk}", default_field='Document.idObjType')
                qs &= Q('query_string', query=f"{group['obj_state']}", default_field='search_data.obj_state')
                # Не показывать заявки, по которым выдан охранный документ
                qs &= ~Q('query_string', query="Document.Status:3 AND search_data.obj_state:1")
                # Показывать только заявки с датой заяки
                qs &= Q('query_string', query="_exists_:search_data.app_date")

                # TODO: для всех показывать только статусы 3 и 4, для вип-ролей - всё.
                # qs &= Q('query_string', query="3 OR 4", default_field='Document.Status')

                qs_list.append(qs)

    # Формирование результирующего запроса
    qs_result = None
    for qs in qs_list:
        if qs_result is None:
            qs_result = qs
        else:
            qs_result |= qs

    client = Elasticsearch(settings.ELASTIC_HOST)
    s = Search(using=client, index="uma").query(qs_result).sort('_score')

    return s


def get_client_ip(request):
    """Возвращает IP-адрес пользователя."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ResultsProxy(object):
    """
    A proxy object for returning Elasticsearch results that is able to be
    passed to a Paginator.
    """
    def __init__(self, s):
        self.s = s

    def __len__(self):
        return self.s.count()

    def __getitem__(self, item):
        return self.s[item.start:item.stop].execute()


def paginate_results(s, page, paginate_by=10):
    """Пагинатор для результов запроса ElasticSearch"""
    paginator = Paginator(ResultsProxy(s), paginate_by)
    page_number = page
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page


def filter_results(s, request):
    """Фильтрует результат запроса ElasticSearch И выполняет агрегацию для фильтров в сайдбаре."""
    # Агрегация для определения всех типов объектов и состояний
    s.aggs.bucket('idObjType_terms', A('terms', field='Document.idObjType'))
    s.aggs.bucket('obj_state_terms', A('terms', field='search_data.obj_state'))
    aggregations = s.execute().aggregations.to_dict()
    s_ = s

    # Фильтрация
    if request.GET.get('filter_obj_type'):
        # Фильтрация в основном запросе
        s = s.filter('terms', Document__idObjType=request.GET.getlist('filter_obj_type'))
        # Агрегация для определения количества объектов определённых типов после применения одного фильтра
        s_filter_obj_type = s_.filter(
            'terms',
            Document__idObjType=request.GET.getlist('filter_obj_type')
        )
        s_filter_obj_type.aggs.bucket('obj_state_terms', A('terms', field='search_data.obj_state'))
        aggregations_obj_state = s_filter_obj_type.execute().aggregations.to_dict()
        for bucket in aggregations['obj_state_terms']['buckets']:
            if not list(filter(lambda x: x['key'] == bucket['key'],
                               aggregations_obj_state['obj_state_terms']['buckets'])):
                aggregations_obj_state['obj_state_terms']['buckets'].append(
                    {'key': bucket['key'], 'doc_count': 0}
                )
        aggregations['obj_state_terms']['buckets'] = aggregations_obj_state['obj_state_terms']['buckets']

    if request.GET.get('filter_obj_state'):
        # Фильтрация в основном запросе
        s = s.filter('terms', search_data__obj_state=request.GET.getlist('filter_obj_state'))
        # Агрегация для определения количества объектов определённых состояний
        # после применения одного фильтра
        s_filter_obj_state = s_.filter(
            'terms',
            search_data__obj_state=request.GET.getlist('filter_obj_state')
        )
        s_filter_obj_state.aggs.bucket('idObjType_terms', A('terms', field='Document.idObjType'))
        aggregations_id_obj_type = s_filter_obj_state.execute().aggregations.to_dict()
        for bucket in aggregations['idObjType_terms']['buckets']:
            if not list(filter(lambda x: x['key'] == bucket['key'],
                               aggregations_id_obj_type['idObjType_terms']['buckets'])):
                aggregations_id_obj_type['idObjType_terms']['buckets'].append(
                    {'key': bucket['key'], 'doc_count': 0}
                )
        aggregations['idObjType_terms']['buckets'] = aggregations_id_obj_type['idObjType_terms']['buckets']

    return s, aggregations


def extend_doc_flow(hit):
    """Расширяет секцию DOCFLOW патента документами заявки"""
    # Получение заявки охранного документа
    q = Q(
        'bool',
        must=[
            Q('match', search_data__app_number=hit.search_data.app_number),
            Q('match', search_data__obj_state=1)
        ]
    )
    client = Elasticsearch(settings.ELASTIC_HOST)
    application = Search().using(client).query(q).execute()
    if application:
        application = application[0]

        try:
            # Объединение стадий
            stages = application.DOCFLOW.STAGES
            stages.extend(hit.DOCFLOW.STAGES)
            hit.DOCFLOW.STAGES = stages
        except AttributeError:
            pass

        try:
            # Объединение документов
            documents = application.DOCFLOW.DOCUMENTS
            documents.extend(hit.DOCFLOW.DOCUMENTS)
            hit.DOCFLOW.DOCUMENTS = documents
        except AttributeError:
            pass

        try:
            # Объединение платежей
            payments = application.DOCFLOW.PAYMENTS
            payments.extend(hit.DOCFLOW.PAYMENTS)
            hit.DOCFLOW.PAYMENTS = payments
        except AttributeError:
            pass

        try:
            # Объединение сборов
            collections = application.DOCFLOW.COLLECTIONS
            collections.extend(hit.DOCFLOW.COLLECTIONS)
            hit.DOCFLOW.COLLECTIONS = collections
        except AttributeError:
            pass


def get_completed_order(order_id, attempts=10, timeout=2):
    """Ждёт пока обрабатывается заказ. Возвращает False если он не обработался."""
    completed = False
    counter = 0
    while completed is False:
        order = OrderService.objects.get(id=order_id)
        if order.order_completed:
            return order
        else:
            if counter == attempts:
                return False
            counter += 1
            time.sleep(timeout)


def create_selection(data_from_json, params):
    """Формирует документ ворд в BytesIO"""
    data = dict()
    data['category'] = data_from_json.pop('Category', None)
    data['contracts_comment'] = data_from_json.pop('Contracts_comment', None)
    data['contracts'] = data_from_json.pop('Contracts', [])
    data['collections_comment'] = data_from_json.pop('Collections_comment', None)
    data['collections'] = data_from_json.pop('Collections', [])
    data['documents_comment'] = data_from_json.pop('Documents_comment', None)
    data['documents'] = data_from_json.pop('Documents', [])
    data['publications_comment'] = data_from_json.pop('Publications_comment', None)
    data['publications'] = data_from_json.pop('Publications', [])
    data['signer_comment'] = data_from_json.pop('Signer_comment', None)
    data['signer'] = data_from_json.pop('Signer', None)
    data['INID_51_HTML'] = data_from_json.pop('INID_51_HTML', None)
    data['main_info_comments'] = list(data_from_json.values())[::2]
    data['main_info_values'] = list(data_from_json.values())[1::2]

    # Формирование выписки
    document = Document('selection_templates/template.docx')

    sections = document.sections
    for section in sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3)
        section.right_margin = Cm(1.5)
        header = section.header
        paragraph = header.paragraphs[0]
        paragraph.text = data['main_info_values'][0]
        paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    paragraph = document.paragraphs[0]
    paragraph_format = paragraph.paragraph_format
    paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph_format.space_after = 0
    paragraph_format.space_before = 0
    run = paragraph.add_run('ВИПИСКА')
    run.bold = True
    run.font.name = 'Times New Roman CYR'
    run.font.size = Pt(18)

    paragraph = document.add_paragraph()
    paragraph_format = paragraph.paragraph_format
    paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph_format.space_after = Pt(18)
    paragraph_format.space_before = 0
    if data['category'] in ('винаходи', 'корисні моделі'):
        run = paragraph.add_run(f"з Державного реєстру патентів України на {data['category']}")
    else:
        run = paragraph.add_run(f"з Державного реєстру свідоцтв України на {data['category']}")
    run.font.name = 'Times New Roman CYR'
    run.font.size = Pt(14)

    table = document.add_table(rows=0, cols=2)
    for i in range(len(data['main_info_comments'])):
        if data['main_info_values'][i] != '':
            row_cells = table.add_row().cells
            row_cells[0].text = data['main_info_comments'][i]
            row_cells[0].paragraphs[0].runs[0].font.bold = True
            row_cells[0].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
            row_cells[0].paragraphs[0].runs[0].font.size = Pt(12)
            row_cells[0].paragraphs[0].space_after = 0
            row_cells[0].paragraphs[0].space_before = 0
            row_cells[1].text = data['main_info_values'][i]
            row_cells[1].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
            row_cells[1].paragraphs[0].runs[0].font.size = Pt(12)
            row_cells[1].paragraphs[0].space_after = 0
            row_cells[1].paragraphs[0].space_before = 0

    if params.get('contracts') and data['contracts_comment'] and len(data['contracts']) > 0:
        paragraph = document.add_paragraph()
        paragraph_format = paragraph.paragraph_format
        paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph_format.space_after = Pt(18)
        paragraph_format.space_before = Pt(18)
        run = paragraph.add_run(data['contracts_comment'])
        run.bold = True
        run.font.name = 'Times New Roman CYR'
        run.font.size = Pt(12)

        for item in data['contracts']:
            item_values = list(item.values())
            comments = item_values[::2]
            values = item_values[1::2]
            table = document.add_table(rows=0, cols=2)
            for i in range(len(comments)):
                if comments[i] != '' and values[i] != '':
                    row_cells = table.add_row().cells
                    row_cells[0].text = comments[i]
                    row_cells[0].paragraphs[0].runs[0].font.bold = True
                    row_cells[0].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
                    row_cells[0].paragraphs[0].runs[0].font.size = Pt(12)
                    row_cells[0].paragraphs[0].space_after = 0
                    row_cells[0].paragraphs[0].space_before = 0
                    row_cells[1].text = values[i]
                    row_cells[1].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
                    row_cells[1].paragraphs[0].runs[0].font.size = Pt(12)
                    row_cells[1].paragraphs[0].space_after = 0
                    row_cells[1].paragraphs[0].space_before = 0
            document.add_paragraph()

    if params.get('collections') and data['collections_comment'] and len(data['collections']) > 0:
        paragraph = document.add_paragraph()
        paragraph_format = paragraph.paragraph_format
        paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(data['collections_comment'])
        run.bold = True
        run.font.name = 'Times New Roman CYR'
        run.font.size = Pt(12)

    if params.get('letters') and data['documents_comment'] and len(data['documents']) > 0:
        paragraph = document.add_paragraph()
        paragraph_format = paragraph.paragraph_format
        paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(data['documents_comment'])
        run.bold = True
        run.font.name = 'Times New Roman CYR'
        run.font.size = Pt(12)

        for item in data['documents']:
            item_values = list(item.values())
            comments = item_values[::2]
            values = item_values[1::2]
            table = document.add_table(rows=0, cols=2)
            for i in range(len(comments)):
                if comments[i] != '' and values[i] != '':
                    row_cells = table.add_row().cells
                    row_cells[0].text = comments[i]
                    row_cells[0].paragraphs[0].runs[0].font.bold = True
                    row_cells[0].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
                    row_cells[0].paragraphs[0].runs[0].font.size = Pt(12)
                    row_cells[0].paragraphs[0].space_after = 0
                    row_cells[0].paragraphs[0].space_before = 0
                    row_cells[1].text = values[i]
                    row_cells[1].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
                    row_cells[1].paragraphs[0].runs[0].font.size = Pt(12)
                    row_cells[1].paragraphs[0].space_after = 0
                    row_cells[1].paragraphs[0].space_before = 0
            document.add_paragraph()

    if params.get('another') and data['publications_comment'] and len(data['publications']) > 0:
        paragraph = document.add_paragraph()
        paragraph_format = paragraph.paragraph_format
        paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(data['publications_comment'])
        run.bold = True
        run.font.name = 'Times New Roman CYR'
        run.font.size = Pt(12)

        for item in data['publications']:
            item_values = list(item.values())
            comments = item_values[::2]
            values = item_values[1::2]
            table = document.add_table(rows=0, cols=2)
            for i in range(len(comments)):
                if comments[i] != '' and values[i] != '':
                    row_cells = table.add_row().cells
                    row_cells[0].text = comments[i]
                    row_cells[0].paragraphs[0].runs[0].font.bold = True
                    row_cells[0].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
                    row_cells[0].paragraphs[0].runs[0].font.size = Pt(12)
                    row_cells[0].paragraphs[0].space_after = 0
                    row_cells[0].paragraphs[0].space_before = 0
                    row_cells[1].text = values[i]
                    row_cells[1].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
                    row_cells[1].paragraphs[0].runs[0].font.size = Pt(12)
                    row_cells[1].paragraphs[0].space_after = 0
                    row_cells[1].paragraphs[0].space_before = 0
            document.add_paragraph()

    paragraph = document.add_paragraph()
    paragraph_format = paragraph.paragraph_format
    paragraph_format.space_after = Pt(18)
    paragraph_format.space_before = Pt(40)
    now = datetime.datetime.now()
    now = now.strftime("%d.%m.%Y")
    run = paragraph.add_run(f"Виписка видана станом на {now} р.")
    run.font.name = 'Times New Roman CYR'
    run.bold = True
    run.font.size = Pt(12)

    table = document.add_table(rows=0, cols=2)
    row_cells = table.add_row().cells
    row_cells[0].text = data['signer']['SignerPost']
    row_cells[0].paragraphs[0].runs[0].font.bold = True
    row_cells[0].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
    row_cells[0].paragraphs[0].runs[0].font.size = Pt(12)
    row_cells[0].paragraphs[0].space_after = 0
    row_cells[0].paragraphs[0].space_before = 0
    row_cells[1].text = data['signer']['SignerName']
    row_cells[1].paragraphs[0].runs[0].font.name = 'Times New Roman CYR'
    row_cells[1].paragraphs[0].runs[0].font.bold = True
    row_cells[1].paragraphs[0].runs[0].font.size = Pt(12)
    row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    row_cells[1].vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
    row_cells[1].paragraphs[0].space_after = 0
    row_cells[1].paragraphs[0].space_before = 0

    paragraph = document.add_paragraph()
    paragraph_format = paragraph.paragraph_format
    paragraph_format.space_before = Pt(18)
    run = paragraph.add_run('М.П.')
    run.font.name = 'Times New Roman CYR'
    run.bold = True
    run.font.size = Pt(12)

    file_stream = io.BytesIO()
    document.save(file_stream)
    file_stream.seek(0)

    return file_stream
