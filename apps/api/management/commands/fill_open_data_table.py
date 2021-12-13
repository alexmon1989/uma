from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.timezone import make_aware
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from apps.search.models import IpcAppList
import apps.api.services as services
from ...models import OpenData
from datetime import datetime
import json


class Command(BaseCommand):
    help = 'Fills open data db table'
    es = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            help='Index only one record with certain idAPPNumber from table IPC_AppLIST'
        )
        parser.add_argument(
            '--not_compare_last_update',
            type=bool,
            help='Do not compare last update field for determining app list for adding to API table'
        )
        parser.add_argument(
            '--obj_type_ids',
            nargs='+',
            type=int,
            help='List of object type ids, space-separated'
        )
        parser.add_argument(
            '--verbose',
            type=bool,
            help='Show progress'
        )

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        # Объекты для добавления в API
        apps = services.app_get_api_list(options)

        if options['verbose']:
            c = len(apps)
            i = 0

        # Добавление/обновление данных
        for d in apps:
            if options['verbose']:
                i += 1
                self.stdout.write(self.style.SUCCESS(f"{i}/{c} - {d[0]}"))

            app_date = None
            app = IpcAppList.objects.get(id=d[0])

            # Получение данных с ElasticSearch
            data = Search(
                using=self.es,
                index=settings.ELASTIC_INDEX_NAME
            ).query(
                "match",
                _id=d[0]
            ).source(
                excludes=["*.DocBarCode", "*.DOCBARCODE"]
            ).execute()

            if data:
                data = data[0].to_dict()

                # Данные заявки из ES (обработанные)
                biblio_data = services.app_get_biblio_data(data)
                data_docs = services.app_get_documents(data)
                data_payments = services.app_get_payments(data)

                if data['Document']['idObjType'] == 4 and data['TradeMark']['TrademarkDetails'].get('ApplicationDate'):
                    app_date = make_aware(
                        datetime.strptime(
                            data['TradeMark']['TrademarkDetails']['ApplicationDate'][:10], '%Y-%m-%d'
                        ),
                        is_dst=True
                    )

                # Сохраннение данных
                open_data_record, created = OpenData.objects.get_or_create(app_id=d[0])
                open_data_record.obj_type_id = app.obj_type_id
                open_data_record.last_update = app.lastupdate
                open_data_record.app_number = app.app_number
                open_data_record.app_date = app_date or app.app_date
                open_data_record.is_visible = True
                open_data_record.data = json.dumps(biblio_data) if biblio_data else None
                open_data_record.data_docs = json.dumps(data_docs) if data_docs else None
                open_data_record.data_payments = json.dumps(data_payments) if data_payments else None
                if app.registration_date:
                    open_data_record.registration_number = app.registration_number
                    open_data_record.registration_date = app.registration_date
                    open_data_record.obj_state = 2
                else:
                    open_data_record.obj_state = 1
                open_data_record.save()

        self.stdout.write(self.style.SUCCESS(f'Finished'))
