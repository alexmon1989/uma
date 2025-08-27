from django.core.management.base import BaseCommand
from django.db import connections

from ...models import IpcAppList

import datetime


class Command(BaseCommand):
    """Сервіс для отримання вихідниї документів по винаходах та корисних моделях, що були відправлені вчора.
    Встановлює запис заявки/патенту як непроіндексований, якщо.
    """

    def _fox_get_app_numbers(self, date: str) -> list[str]:
        with connections['ellav'].cursor() as cursor:
            query = f"""
                SELECT *
                FROM OPENQUERY([FOX,51433], 'select
                        rc.inputNumber
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
                        ad1.value = ''{date}''
                    
                    UNION
                    
                    select    
                        rc.inputNumber
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
                        ad1.value = ''{date}''')
            """
            cursor.execute(query)
            results = cursor.fetchall()
            return results

    def handle(self, *args, **options) -> None:
        yesterday = (datetime.datetime.now() - datetime.timedelta(1)).strftime('%Y-%m-%d')
        results = self._fox_get_app_numbers(yesterday)
        for item in results:
            IpcAppList.objects.filter(app_number=item[0]).update(elasticindexed=0)
        print('Finished')
