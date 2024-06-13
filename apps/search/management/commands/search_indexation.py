import logging

from django.core.management.base import BaseCommand

from apps.search.services.application_indexators import ApplicationIndexationService
from apps.search.models import IpcAppList


# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        apps = IpcAppList.objects.filter(obj_type_id=4, elasticindexed=0)
        for app in apps:
            service = ApplicationIndexationService(app)
            if service.index():
                print(app.app_number)
