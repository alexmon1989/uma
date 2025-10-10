from django.core.management.base import BaseCommand
from django.db import connections

from ...models import PatentAttorneyNew
from ...services import patent_attorney_fill_db_from_file, patent_attorney_fill_db_old_db


class Command(BaseCommand):
    help = 'Fills patent_attorneys db table'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str, help='Input filename')

    def handle(self, *args, **options):
        with connections['default'].cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {PatentAttorneyNew._meta.db_table}")

        patent_attorney_fill_db_from_file(options['filename'])
        patent_attorney_fill_db_old_db()
