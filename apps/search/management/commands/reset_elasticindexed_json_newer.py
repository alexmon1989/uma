from django.core.management.base import BaseCommand
from django.db import connections

from ...models import IpcAppList

import datetime
import os


class Command(BaseCommand):
    """Сервіс для визначення заявок (ТМ, ПЗ), по яким було оновлення файлу .json з даними, але не було оновлено дані у БД.
    Для таких заявок поле elasticindexed у БД скидається на 0 (маркер необхідності переіндексації).
    """

    def handle(self, *args, **options) -> None:
        # Отримання номерів заявок, які були оновлені
        today = datetime.date.today()
        day_back = today - datetime.timedelta(days=2)
        with connections['prod_erp_cms_import'].cursor() as cursor:
            query = f"""
                    SELECT DISTINCT claim_number, type_code
                    FROM fv_cic_importer
                    WHERE is_exported_datetime > '{day_back}' AND is_exported = '1'
            """
            cursor.execute(query)
            results = cursor.fetchall()

        trademarks = [x[0] for x in results if x[1] == 'TORGOVI_MARKY']
        designs = [x[0] for x in results if x[1] == 'PROM_ZNAK']

        # Отримання даних заявок з БД СІС
        apps = IpcAppList.objects.filter(
            obj_type=4,
            app_number__in=trademarks
        ).union(
            IpcAppList.objects.filter(
                obj_type=6,
                app_number__in=designs
            )
        )

        # Перевірка чи новіший файл .json від запису в БД, скидання маркеру індексації
        res = []
        for app in apps:
            file_name = app.registration_number \
                if (app.registration_number and app.registration_number != '0') \
                else app.app_number
            file_name = file_name.replace('/', '_')

            file_path = os.path.join(app.real_files_path, f"{file_name}.json")

            try:
                mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                if mod_date > app.lastupdate:
                    res.append(app.app_number)
                    app.elasticindexed = 0
                    app.save()
            except FileNotFoundError:
                pass

        print('Finished')
