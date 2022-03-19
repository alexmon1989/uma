from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from asgiref.sync import sync_to_async
import asyncio


class Command(BaseCommand):
    _index_fn = None
    _es_search = None
    es = None
    sem = None
    total_count = 0
    finished = 0

    async def process_app(self, app_id):
        s = await self._es_search(index=settings.ELASTIC_INDEX_NAME, body={"query": {"match": {'_id': app_id}}})

        body = s['hits']['hits'][0]['_source']

        design_details = body['Design']['DesignDetails']

        if design_details.get('RecordPublicationDetails'):
            for x in design_details['RecordPublicationDetails']:
                if len(x.get('PublicationIdentifier')) < 6:
                    x['PublicationIdentifier'] = f"{x['PublicationIdentifier']}/{x['PublicationDate'][:4]}"

        await self._index_fn(index=settings.ELASTIC_INDEX_NAME,
                             doc_type='_doc',
                             id=app_id,
                             body=body,
                             request_timeout=30)

        self.finished += 1
        print(f'processed {self.finished}/{self.total_count} - {app_id}')

    async def safe_process_app(self, app_id):
        async with self.sem:  # semaphore limits num of simultaneous downloads
            return await self.process_app(app_id)

    async def main(self):
        # Получение заявок
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        query = Q(
            'query_string',
            query="Document.idObjType:6 AND search_data.obj_state:2"
        )
        s = Search().using(self.es).query(query)
        self.total_count = s.count()

        self.sem = asyncio.Semaphore(1000)
        self._index_fn = sync_to_async(self.es.index)
        self._es_search = sync_to_async(self.es.search)
        tasks = []
        for i, h in enumerate(s.scan()):
            await asyncio.sleep(0)
            tasks.append(asyncio.ensure_future(self.safe_process_app(h.meta.id)))
        await asyncio.gather(*tasks)

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.main())
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()
