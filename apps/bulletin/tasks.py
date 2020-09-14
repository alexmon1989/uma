from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from celery import shared_task
from django.conf import settings
from .utils import prepare_tm_data, prepare_madrid_tm_data


@shared_task
def get_app_details(app_number):
    """Задача для получения деталей по заявке."""
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

    # Получение объекта из индекса
    q = Q(
        'bool',
        should=[
            Q('match', search_data__app_number=app_number),
            Q('match', search_data__protective_doc_number=app_number)
        ],
        minimum_should_match=1
    )
    s = Search().using(client).query(q).execute()
    if not s:
        return {}
    hit = s[0].to_dict()

    biblio_data = dict()

    if hit['Document']['idObjType'] in (1, 2, 3):
        biblio_data = hit['Claim'] if hit['search_data']['obj_state'] == 1 else hit['Patent']

    elif hit['Document']['idObjType'] == 4:
        biblio_data = prepare_tm_data(s[0])

    elif hit['Document']['idObjType'] == 6:
        biblio_data = hit['Design']['DesignDetails']

    elif hit['Document']['idObjType'] == 9:
        biblio_data = prepare_madrid_tm_data(s[0])

    return biblio_data
