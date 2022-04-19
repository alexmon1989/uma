from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch('10.11.11.51:9200', timeout=60)
        query = Q(
            'bool',
            must=[
                Q(
                    "nested",
                    path="search_data.agent",
                    query=Q(
                        "query_string",
                        query="NOT _exists_:search_data.agent.name"
                    )
                ),
                Q(
                    "query_string",
                    query="Document.idObjType:1 OR Document.idObjType:2 OR Document.idObjType:3"
                )
            ]
        )

        s = Search(index='uma3').using(es).query(query)
        c = s.count()



        i = 0

        for h in s.params(size=10).scan():
            i += 1
            print(f"{i}/{c} - {h.meta.id}")

            biblio_data = None

            body = h.to_dict()
            if body.get('Patent'):
                biblio_data = body['Patent']
            elif body.get('Claim'):
                biblio_data = body['Claim']

            if biblio_data.get('I_74'):
                body['search_data']['agent'] = [{'name': biblio_data.get('I_74')}]
            else:
                del body['search_data']['agent']

            es.index(index='uma3',
                     doc_type='_doc',
                     id=h.meta.id,
                     body=body,
                     request_timeout=60)
