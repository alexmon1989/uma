from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from celery import shared_task
from django.conf import settings
import os
from ..search.utils import sort_results, prepare_data_for_search_report, create_search_res_doc
from uma.utils import get_unique_filename, get_user_or_anonymous


@shared_task
def create_favorites_results_file(user_id, favorites_ids, get_params, lang_code):
    """Возвращает url файла с результатами содержимого в избранном."""
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

        s = s.source(['search_data', 'Document', 'Claim'])

        # Данные для Excel-файла
        user = get_user_or_anonymous(user_id)
        data = prepare_data_for_search_report(s, lang_code, user)

        # Формировние Excel-файла
        workbook = create_search_res_doc(data)

        directory_path = os.path.join(
            settings.MEDIA_ROOT,
            'search_results',
        )
        os.makedirs(directory_path, exist_ok=True)
        # Имя файла с результатами поиска
        file_name = f"{get_unique_filename('favorites')}.xls"
        file_path = os.path.join(directory_path, file_name)

        # Сохранение файла
        workbook.save(file_path)

        # Возврат url сформированного файла с результатами поиска
        return os.path.join(
            settings.MEDIA_URL,
            'search_results',
            file_name
        )
    return False
