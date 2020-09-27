from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.timezone import make_aware
from django.db.models import Max
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from apps.search.models import IpcAppList
from apps.bulletin.models import EBulletinData
from ...models import OpenData
import json


class Command(BaseCommand):
    help = 'Fills open data db table'
    es = None

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        # Получение максимальной даты обновления в таблице с данными для OpenData
        max_date = OpenData.objects.aggregate(Max('last_update'))['last_update__max']

        # Получение данных всех объектов, дата обновления у которых больше max_date,
        # обновление их в таблице с данными для OpenData
        items = IpcAppList.objects.filter(
            elasticindexed=1
        ).exclude(
            registration_date__isnull=True, obj_type_id__in=(1, 2, 3, 5, 6)  # исключить заявки не на ТМ
        ).order_by('lastupdate')

        if max_date:
            items = items.filter(lastupdate__gt=max_date)

        for item in items:
            open_data_record, created = OpenData.objects.get_or_create(
                app_id=item.pk
            )
            # Обновление данных, если это необходимо
            if open_data_record.last_update != make_aware(item.lastupdate) or len(open_data_record.data) == 0:
                open_data_record.obj_type_id = item.obj_type_id
                open_data_record.last_update = make_aware(item.lastupdate)
                open_data_record.app_number = item.app_number
                open_data_record.app_date = item.app_date
                if item.registration_date:
                    open_data_record.registration_number = item.registration_number
                    open_data_record.registration_date = make_aware(item.registration_date)
                    open_data_record.obj_state = 2
                else:
                    open_data_record.obj_state = 1

                # Получение данных с ElasticSearch
                data = Search(using=self.es, index=settings.ELASTIC_INDEX_NAME).query("match", _id=item.id).execute()

                if data:
                    data = data[0].to_dict()
                    try:
                        data_to_write = {}
                        # Патенты на изобретения, Патенты на полезные модели, Свидетельства на топографии инт. микросхем
                        if item.obj_type_id in (1, 2, 3):
                            data_to_write = data['Patent']
                        # Свидетельства на знаки для товаров и услуг
                        elif item.obj_type_id == 4:
                            data_to_write = data['TradeMark']['TrademarkDetails']

                            if data['search_data']['obj_state'] == 1:
                                # Статус заявки
                                mark_status_code = int(data['Document'].get('MarkCurrentStatusCodeType', 0))
                                is_stopped = data['Document'].get(
                                    'RegistrationStatus') == 'Діловодство за заявкою припинено' or mark_status_code == 8000
                                if is_stopped:
                                    data_to_write['application_status'] = 'stopped'
                                else:
                                    data_to_write['application_status'] = 'active'

                            if data_to_write.get('Code_441') is None:
                                # Поле 441 (дата опублікования заявки)
                                try:
                                    e_bulletin_app = EBulletinData.objects.get(
                                        app_number=data_to_write.get('ApplicationNumber')
                                    )
                                except EBulletinData.DoesNotExist:
                                    pass
                                else:
                                    data_to_write['Code_441'] = str(e_bulletin_app.publication_date)
                        # Свидетельства на КЗПТ
                        elif item.obj_type_id == 5:
                            data_to_write = data['Geo']['GeoDetails']
                        # Патенты на пром. образцы
                        elif item.obj_type_id == 6:
                            data_to_write = data['Design']['DesignDetails']

                        if data['search_data']['obj_state'] == 2:
                            data_to_write['registration_status_color'] = data['search_data']['registration_status_color']
                    except KeyError as e:
                        self.stdout.write(
                            self.style.ERROR(f"Can't get app data (idAPPNumber={item.id}, error text:{e})")
                        )
                    else:
                        open_data_record.data = json.dumps(data_to_write)

                # Сохранение в БД
                open_data_record.save()

        self.stdout.write(self.style.SUCCESS(f'Finished'))
