from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from asgiref.sync import sync_to_async
import asyncio


class Command(BaseCommand):

    async def main(self):
        # Получение заявок
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main())
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
