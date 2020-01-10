from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from ...utils import get_registration_status_color
import traceback


class Command(BaseCommand):
    help = 'Sets registration_status_color for ES records'

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        query = Q(
            "match",
            search_data__obj_state=2,
        ) & ~Q(
            'query_string',
            query="_exists_:search_data.registration_status_color"
        )
        s = Search().using(es).query(query)
        for h in s.scan():
            body = h.to_dict()
            try:
                body['search_data']['registration_status_color'] = get_registration_status_color(body)
            except:
                self.stdout.write(self.style.ERROR(f"Error in {h.meta.id}"))
                error_traceback = traceback.format_exc()
                self.stdout.write(error_traceback)
            es.index(index=settings.ELASTIC_INDEX_NAME,
                     doc_type='_doc',
                     id=h.meta.id,
                     body=body,
                     request_timeout=30)
        self.stdout.write(self.style.SUCCESS('Finished'))
