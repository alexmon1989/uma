from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from apps.search.models import IpcAppList
from ...utils import get_registration_status_color
import traceback


class Command(BaseCommand):
    help = 'Sets registration_status_color for ES records'

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        query = Q(
            'query_string',
            query="TradeMark.DocFlow.Documents.DocRecord.DocType:\"ТМ-9\""
        )
        s = Search().using(es).query(query)

        for h in s.scan():
            app = IpcAppList.objects.get(pk=h.meta.id)
            app.elasticindexed = 0
            app.save()
        self.stdout.write(self.style.SUCCESS('Finished'))
