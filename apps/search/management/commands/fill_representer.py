from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        t = {
            4: ['TradeMark', 'TrademarkDetails'],
            6: ['Design', 'DesignDetails'],
        }

        query = Q(
            "query_string",
            query="Document.idObjType:4 OR Document.idObjType:6"
        )
        s = Search().using(es).query(query)
        c = s.count()
        i = 0

        for h in s.scan():
            body = h.to_dict()

            i += 1
            print(f"{i}/{c} - {body['search_data']['app_number']} - {h.meta.id}")

            representers = []

            body_details = body[t[body['Document']['idObjType']][0]][t[body['Document']['idObjType']][1]]

            for representer in body_details.get('RepresentativeDetails', {}).get('Representative', []):
                if representer.get('RepresentativeAddressBook'):
                    if body['Document']['idObjType'] == 4:
                        name = representer['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                            'FreeFormatNameDetails']['FreeFormatNameDetails']['FreeFormatNameLine']
                    else:
                        name = representer['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                            'FreeFormatNameDetails']['FreeFormatNameLine']
                    address = representer['RepresentativeAddressBook']['FormattedNameAddress']['Address']['FreeFormatAddress']['FreeFormatAddressLine']
                    representers.append(f"{name}, {address}")

            if representers:
                body['search_data']['agent'] = representers
                es.index(index=settings.ELASTIC_INDEX_NAME,
                         doc_type='_doc',
                         id=h.meta.id,
                         body=body,
                         request_timeout=30)
