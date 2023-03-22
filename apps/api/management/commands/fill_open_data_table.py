from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from apps.search.models import IpcAppList
import apps.api.services as api_services
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

    def get_registration_date(self, app: IpcAppList, data: dict) -> datetime | str:
        """Возвращает дату регистрации."""
        if data['Document']['idObjType'] in (1, 2, 3):
            registration_date = data['Patent']['I_24']
        elif data['Document']['idObjType'] == 4:
            registration_date = data['TradeMark']['TrademarkDetails'].get('RegistrationDate')
        elif data['Document']['idObjType'] == 6:
            registration_date = data['Design']['DesignDetails'].get('RecordEffectiveDate')
        else:
            registration_date = app.registration_date
        return registration_date or app.registration_date

    def get_app_date(self, app: IpcAppList, data: dict) -> datetime | str:
        """Возвращает дату заявки."""
        if data['Document']['idObjType'] == 4 and data['TradeMark']['TrademarkDetails'].get('ApplicationDate'):
            return data['TradeMark']['TrademarkDetails']['ApplicationDate'][:10]
        elif data['Document']['idObjType'] == 6 and data['Design']['DesignDetails'].get('DesignApplicationDate'):
            return data['Design']['DesignDetails']['DesignApplicationDate'][:10]
        else:
            return app.app_date

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        # Объекты для добавления в API
        apps = api_services.app_get_api_list(options)

        if options['verbose']:
            c = len(apps)
            i = 0

        # Добавление/обновление данных
        for d in apps:
            if options['verbose']:
                i += 1
                self.stdout.write(self.style.SUCCESS(f"{i}/{c} - {d[0]}"))

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
                biblio_data = api_services.app_get_biblio_data(data)
                data_docs = api_services.app_get_documents(data)
                data_payments = api_services.app_get_payments(data)

                # Сохраннение данных
                open_data_record, created = OpenData.objects.get_or_create(app_id=d[0])
                open_data_record.obj_type_id = app.obj_type_id
                open_data_record.last_update = app.lastupdate
                open_data_record.app_number = app.app_number
                open_data_record.app_date = self.get_app_date(app, data)
                open_data_record.files_path = app.files_path
                open_data_record.data = json.dumps(biblio_data) if biblio_data else None
                open_data_record.data_docs = json.dumps(data_docs) if data_docs else None
                open_data_record.data_payments = json.dumps(data_payments) if data_payments else None
                if app.registration_date:
                    open_data_record.registration_number = app.registration_number
                    open_data_record.registration_date = self.get_registration_date(app, data)
                    open_data_record.obj_state = 2
                else:
                    open_data_record.obj_state = 1
                open_data_record.save()

        self.stdout.write(self.style.SUCCESS(f'Finished'))
