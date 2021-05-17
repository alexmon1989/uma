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
        apps = IpcAppList.objects.filter(
            elasticindexed=1
        ).exclude(
            obj_type_id__in=(1, 2, 3, 5, 6), registration_date__isnull=True
        ).exclude(
            obj_type_id__in=(9, 11, 12, 14)
        ).annotate(
            app_id=F('id'), last_update=F('lastupdate')
        ).values_list('app_id', 'last_update')

        # Объекты в API
        api_apps = OpenData.objects.values_list('app_id', 'last_update')

        # Объекты, которых нет в API (или которые имеют другое значение поля last_update)
        diff = list(set(apps) - set(api_apps))

        c = len(diff)
        i = 0

        # Добавление/обновление данных
        for d in diff:
            i += 1
            print(f"{i}/{c}")
            is_visible = True
            app_date = None
            app = IpcAppList.objects.get(id=d[0])

            # Получение данных с ElasticSearch
            data = Search(using=self.es, index=settings.ELASTIC_INDEX_NAME).query("match", _id=d[0]).execute()
            if data:
                data = data[0].to_dict()
                try:
                    data_to_write = {}
                    # Патенты на изобретения, Патенты на полезные модели, Свидетельства на топографии инт. микросхем
                    if app.obj_type_id in (1, 2, 3):
                        data_to_write = data['Patent']

                    # Свидетельства на знаки для товаров и услуг
                    elif app.obj_type_id == 4:
                        data_to_write = data['TradeMark']['TrademarkDetails']

                        if data['TradeMark']['TrademarkDetails'].get('ApplicationDate'):
                            app_date = make_aware(
                                datetime.strptime(
                                    data['TradeMark']['TrademarkDetails']['ApplicationDate'][:10],
                                    '%Y-%m-%d'
                                ), is_dst=True
                            )

                        if data['search_data']['obj_state'] == 1:
                            # Статус заявки
                            mark_status_code = int(data['Document'].get('MarkCurrentStatusCodeType', 0))
                            is_stopped = data['Document'].get('RegistrationStatus') == 'Діловодство за заявкою припинено' or mark_status_code == 8000
                            if is_stopped:
                                data_to_write['application_status'] = 'stopped'
                            else:
                                data_to_write['application_status'] = 'active'

                        if data_to_write.get('Code_441') is None:
                            # Поле 441 (дата опубликования заявки)
                            try:
                                e_bulletin_app = EBulletinData.objects.get(
                                    app_number=data_to_write.get('ApplicationNumber')
                                )
                            except EBulletinData.DoesNotExist:
                                # Если это заявка
                                if data['search_data']['obj_state'] == 1:
                                    # и её дата подачи после 18.07.2020, то публиковать её нельзя
                                    if app.app_date > make_aware(datetime.strptime('2020-07-17', '%Y-%m-%d')):
                                        is_visible = False
                                    else:
                                        is_visible = mark_status_code > 2000
                            else:
                                data_to_write['Code_441'] = str(e_bulletin_app.publication_date)

                    # Свидетельства на КЗПТ
                    elif app.obj_type_id == 5:
                        data_to_write = data['Geo']['GeoDetails']

                    # Патенты на пром. образцы
                    elif app.obj_type_id == 6:
                        data_to_write = data['Design']['DesignDetails']

                    elif app.obj_type_id in (10, 13):  # Авторське право
                        data_to_write = data['Certificate']['CopyrightDetails']

                    if data['search_data']['obj_state'] == 2:
                        data_to_write['registration_status_color'] = data['search_data'][
                            'registration_status_color']
                except KeyError as e:
                    self.stdout.write(
                        self.style.ERROR(f"Can't get app data (idAPPNumber={app.id}, error text:{e})")
                    )
                else:
                    # Сохраннение данных
                    open_data_record, created = OpenData.objects.get_or_create(app_id=d[0])
                    open_data_record.obj_type_id = app.obj_type_id
                    open_data_record.last_update = app.lastupdate
                    open_data_record.app_number = app.app_number
                    open_data_record.app_date = app_date or app.app_date
                    open_data_record.is_visible = is_visible
                    open_data_record.data = json.dumps(data_to_write)
                    if app.registration_date:
                        open_data_record.registration_number = app.registration_number
                        open_data_record.registration_date = app.registration_date
                        open_data_record.obj_state = 2
                    else:
                        open_data_record.obj_state = 1
                    open_data_record.save()

        self.stdout.write(self.style.SUCCESS(f'Finished'))
