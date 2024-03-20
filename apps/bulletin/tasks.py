from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from celery import shared_task
from django.conf import settings
from .utils import prepare_tm_data, prepare_madrid_tm_data, prepare_kzpt_data
from .models import EBulletinData


@shared_task
def get_app_details(app_number):
    """Задача для получения деталей по заявке."""
    # Проверка существует ли заявка в отдельной таблице с 441-ми кодами
    if not EBulletinData.objects.filter(app_number=app_number, publication_date__lt='2024-03-20').exists():
        return {}

    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

    # Получение объекта из индекса
    q = Q(
        'bool',
        should=[
            Q('bool', must=[
                Q('match', search_data__app_number=app_number),
            ]),
        ],
        minimum_should_match=1
    )
    s = Search(index=settings.ELASTIC_INDEX_NAME).using(client).query(q).source(
        excludes=["*.DocBarCode", "*.DOCBARCODE"]
    ).execute()
    if not s:
        return {}
    hit = s[0].to_dict()

    biblio_data = dict()
    # Формирование словаря с данными заявки
    if hit['Document']['idObjType'] == 4:
        biblio_data = prepare_tm_data(s[0])

    elif hit['Document']['idObjType'] == 5:
        biblio_data = prepare_kzpt_data(s[0])

    elif hit['Document']['idObjType'] in (9, 14):
        biblio_data = prepare_madrid_tm_data(app_number, s[0])

    return biblio_data
