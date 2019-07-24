from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Search
from apps.search.models import IpcAppList
from ...models import OpenData
import json

class Command(BaseCommand):
    help = 'Fills open data db table'
    es = None

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        self.es = Elasticsearch(settings.ELASTIC_HOST)

        # Выборка всех охранных документов из ElasticSearch
        q = Q(
            'query_string',
            query='search_data.obj_state:2'
        )
        s = Search(using=self.es, index=settings.ELASTIC_INDEX_NAME).query(q)

        # Добавление в БД
        for h in s.params(size=100, preserve_order=True).scan():
            app = IpcAppList.objects.get(id=h.meta.id)

            data = h.to_dict()
            # Патенты на изобретения, Патенты на полезные модели, Свидетельства на топографии инт. микросхем
            if app.obj_type_id in (1, 2, 3):
                data = data['Patent']
            # Свидетельства на знаки для товаров и услуг
            elif app.obj_type_id == 4:
                data = data['TradeMark']['TrademarkDetails']
            # Свидетельства на КЗПТ
            elif app.obj_type_id == 5:
                data = data['Geo']['GeoDetails']
            # Патенты на пром. образцы
            elif app.obj_type_id == 6:
                data = data['Design']['DesignDetails']

            open_data_record, created = OpenData.objects.get_or_create(app=app)
            open_data_record.data = json.dumps(data)
            open_data_record.save()

        self.stdout.write(self.style.SUCCESS('Finished'))
