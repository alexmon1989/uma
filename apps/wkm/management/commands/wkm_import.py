from django.core.management.base import BaseCommand

from apps.wkm.models import WKMMark
from apps.wkm.services import WKMImportService


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:
        marks = WKMMark.objects.prefetch_related('wkmclass_set').all()
        for wkm in marks:
            service = WKMImportService(wkm=wkm)
            service.execute()
