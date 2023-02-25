from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from celery import shared_task

from django.conf import settings

import os
from typing import List
from pathlib import Path

from ..search.utils import sort_results, prepare_data_for_search_report, create_search_res_doc, filter_app_data
from ..search.services.reports import ReportWriterDocxCreator
from ..search.services import services as search_services
from uma.utils import get_unique_filename, get_user_or_anonymous


@shared_task
def create_favorites_results_file_xlsx(user_id, favorites_ids, get_params, lang_code):
    """Возвращает url файла (.xlsx) с результатами содержимого в избранном."""
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    q = Q(
        'bool',
        must=[Q('terms', _id=favorites_ids)],
    )
    s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(q)

    if s.count() <= 5000:
        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        # Данные для Excel-файла
        user = get_user_or_anonymous(user_id)
        # Данные для Excel-файла
        data = prepare_data_for_search_report(s, lang_code, user)

        directory_path = os.path.join(
            settings.MEDIA_ROOT,
            'search_results',
        )
        os.makedirs(directory_path, exist_ok=True)
        # Имя файла с результатами поиска
        file_name = f"{get_unique_filename('favorites')}.xlsx"
        file_path = os.path.join(directory_path, file_name)

        # Формировние и сохранение Excel-файла
        create_search_res_doc(data, file_path)

        # Возврат url сформированного файла с результатами поиска
        return os.path.join(
            settings.MEDIA_URL,
            'search_results',
            file_name
        )
    return False


@shared_task
def create_favorites_results_file_docx(user_id: int, favorites_ids: List[int], get_params: dict, lang_code: str):
    """Возвращает url файла (.docx) с результатами содержимого в избранном."""
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    q = Q(
        'bool',
        must=[Q('terms', _id=favorites_ids)],
    )
    s = Search(using=client, index=settings.ELASTIC_INDEX_NAME).query(q)

    if s.count() <= 5000:
        # Сортировка
        if get_params.get('sort_by'):
            s = sort_results(s, get_params['sort_by'][0])
        else:
            s = s.sort('_score')

        directory_path = Path(settings.MEDIA_ROOT) / 'search_results'
        os.makedirs(str(directory_path), exist_ok=True)

        # Имя файла с результатами поиска
        file_name = f"{get_unique_filename('favorites')}.docx"
        file_path = directory_path / file_name

        # Получение заявок и фильтрация данных
        user = get_user_or_anonymous(user_id)
        applications = [filter_app_data(x.to_dict(), user) for x in s.params(size=1000, preserve_order=True).scan()]

        # Генерация отчёта
        report_writer = ReportWriterDocxCreator.create(
            applications,
            search_services.inid_code_get_list(lang_code)
        )
        report_writer.generate(file_path)

        # Возврат url сформированного файла с результатами поиска
        res = Path(settings.MEDIA_URL) / 'search_results' / file_name
        return str(res)
    return False
