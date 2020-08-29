from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from apps.bulletin.models import EBulletinData


class Command(BaseCommand):
    help = 'Adds 441 code to TM applications'

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        c = EBulletinData.objects.count()
        i = 0
        for app in EBulletinData.objects.all():
            query = Q(
                'query_string',
                query=f"search_data.app_number:{app.app_number} AND search_data.obj_state:1"
            )
            s = Search().using(es).query(query).execute()
            if s:
                hit = s[0].to_dict()
                hit['TradeMark']['TrademarkDetails']['Code_441'] = app.publication_date
                es.index(index=settings.ELASTIC_INDEX_NAME,
                         doc_type='_doc',
                         id=s[0].meta.id,
                         body=hit,
                         request_timeout=30)
            i += 1
            print(f"{i}/{c}")

        self.stdout.write(self.style.SUCCESS('Finished'))
