from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import F
from django.utils.timezone import make_aware
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from apps.search.models import IpcAppList
from apps.bulletin.models import EBulletinData
from ...models import OpenData
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Fills open data db table'
    es = None

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        # Объекты для добавления в API
        apps = OpenData.objects.filter(
            data_docs__isnull=True
        ).values('app_id', 'obj_type_id')

        c = apps.count()
        i = 0

        # Добавление/обновление данных
        for app in apps:
            i += 1
            print(f"{i}/{c} - {app['app_id']}")

            # Получение данных с ElasticSearch
            data = Search(using=self.es, index=settings.ELASTIC_INDEX_NAME).query("match", _id=app['app_id']).execute()
            if data:
                data = data[0].to_dict()
                try:
                    data_docs = None
                    # Патенты на изобретения, Патенты на полезные модели, Свидетельства на топографии инт. микросхем
                    if app['obj_type_id'] in (1, 2, 3):
                        data_docs = data.get('DOCFLOW', {}).get('DOCUMENTS')

                    # Свидетельства на знаки для товаров и услуг
                    elif app['obj_type_id'] == 4:
                        data_docs = data['TradeMark'].get('DocFlow', {}).get('Documents')

                    # Патенты на пром. образцы
                    elif app['obj_type_id'] == 6:
                        data_docs = data['Design'].get('DocFlow', {}).get('Documents')

                except KeyError as e:
                    self.stdout.write(
                        self.style.ERROR(f"Can't get app data (idAPPNumber={app['app_id']}, error text:{e})")
                    )
                else:
                    # Сохраннение данных
                    OpenData.objects.filter(app_id=app['app_id']).update(data_docs=json.dumps(data_docs))

        self.stdout.write(self.style.SUCCESS(f'Finished'))
