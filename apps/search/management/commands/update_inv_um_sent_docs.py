from django.core.management.base import BaseCommand
from django.db import connections

from ...models import IpcAppList

import datetime


class Command(BaseCommand):
    """Сервіс для отримання вихідниї документів по винаходах та корисних моделях, що були відправлені вчора.
    Встановлює запис заявки/патенту як непроіндексований.
    """
    _date: str

    def _fox_get_applications(self) -> list[str]:
        with connections['ellav'].cursor() as cursor:
            query = f"""
                SELECT *
                FROM OPENQUERY([FOX,51433], 'select
                        DISTINCT rc.inputNumber
                    from
                        VP3.dbo.rr_exp_claim rc
                        join VP3.dbo.link_object lo on (
                          lo.idreestr1 = 204 and lo.idobject1 = rc.id
                          and lo.idreestr2 = 205 and lo.idlink = 105
                        )
                        left join VP3.dbo.ap_date ad1 on (
                          ad1.idreestr = 205 and ad1.idobject = lo.idobject2 and ad1.idlink = 230
                        )
                    where
                        ad1.value = ''{self._date}''')
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results

    def _fox_get_patents(self) -> list[str]:
        with connections['ellav'].cursor() as cursor:
            query = f"""
                SELECT *
                FROM OPENQUERY([FOX,51433], '
                    select    
                        DISTINCT rc.inputNumber
                    from
                        VP3.dbo.rr_patent rc
                        join VP3.dbo.link_object lo on (
                          lo.idreestr1 = 224 and lo.idobject1 = rc.id
                          and lo.idreestr2 = 205 and lo.idlink = 105
                        )
                        left join VP3.dbo.ap_date ad1 on (
                          ad1.idreestr = 205 and ad1.idobject = lo.idobject2 and ad1.idlink = 230
                        )
                        left join VP3.dbo.ap_date ai on (
                          ai.idreestr = 205 and ai.idobject = lo.idobject2 and ai.idlink = 417
                        )
                    where
                        ad1.value > ''{self._date}''')
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results

    def handle(self, *args, **options) -> None:
        d = (datetime.datetime.now() - datetime.timedelta(2)).strftime('%Y-%m-%d')
        self._date = d

        applications = self._fox_get_applications()
        for item in applications:
            IpcAppList.objects.filter(
                app_number=item[0],
                obj_type_id__in=[1, 2],
                registration_date__isnull=True
            ).update(
                elasticindexed=0
            )

        patents = self._fox_get_patents()
        for item in patents:
            IpcAppList.objects.filter(
                app_number=item[0],
                obj_type_id__in=[1, 2],
                registration_date__isnull=False
            ).update(
                elasticindexed=0
            )

        print('Finished')
