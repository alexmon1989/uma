from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from ...models import OpenData


class Command(BaseCommand):
    help = 'Sets is_visible field'

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        query = Q(
            'query_string',
            query="search_data.obj_state:1 "
                  "AND Document.idObjType:4 "
                  "AND search_data.app_date:[* TO 2020-07-18] "
                  "AND Document.MarkCurrentStatusCodeType:[* TO 2000]"
        )
        s = Search().using(es).query(query)
        for h in s.scan():
            o = OpenData.objects.get(app_number=h.search_data.app_number)
            o.is_visible = False
            o.save()

        self.stdout.write(self.style.SUCCESS('Finished'))
