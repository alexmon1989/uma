from django.core.management.base import BaseCommand

from apps.search.services.sis_importer import GeoSisImporter


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:
        self.stdout.write('Start geo importing process')
        service = GeoSisImporter()
        service.execute()
        self.stdout.write(self.style.SUCCESS('Finished'))
