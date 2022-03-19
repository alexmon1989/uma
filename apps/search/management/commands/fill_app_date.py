from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from apps.search.models import IpcAppList
from apps.bulletin.models import EBulletinData

import csv
import datetime


class Command(BaseCommand):

    def handle(self, *args, **options):
        not_exist = []
        i = 0
        with open('expdata.csv', newline='') as File:
            reader = csv.reader(File, delimiter=';')
            for row in reader:
                i += 1
                try:
                    app = IpcAppList.objects.get(app_number=row[0])
                except IpcAppList.DoesNotExist:
                    not_exist.append(row[0])
                    print(f"{row[0]} - does not exist")
                else:
                    publication_app_date = row[1][:10]
                    app.publication_app_date = datetime.datetime.strptime(
                        publication_app_date, '%d.%m.%Y'
                    ).strftime('%Y-%m-%d')
                    app.lastupdate = datetime.datetime.now()
                    app.elasticindexed = 0
                    app.save()

                    bulletin_item, created = EBulletinData.objects.get_or_create(app_number=row[0])
                    if created:
                        bulletin_item.publication_date = app.publication_app_date
                        bulletin_item.unit_id = 1
                        bulletin_item.save()
                        print(f"{row[0]} - bulletin item created")

                    print(f"{i}: {row[0]} - done")

        if not_exist:
            print(not_exist)

        self.stdout.write(self.style.SUCCESS('Finished'))
