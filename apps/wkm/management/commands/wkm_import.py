from django.core.management.base import BaseCommand

from apps.wkm.models import WKMMark


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:
        marks = WKMMark.objects.prefetch_related('wkmclass_set').using('WellKnownMarks').all()
        for mark in marks:
            print(mark.to_dict())
