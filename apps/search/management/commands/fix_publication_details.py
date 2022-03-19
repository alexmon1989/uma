from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
import datetime


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        query = Q(
            'query_string',
            query="Document.idObjType:4 AND search_data.obj_state:2"
        )
        s = Search().using(es).query(query)
        c = s.count()
        i = 0
        for h in s.scan():
            body = h.to_dict()

            i += 1
            print(f"apps: {i}/{c} - {h.meta.id}")

            trademark_details = body['TradeMark']['TrademarkDetails']
            try:
                if trademark_details.get('PublicationDetails', {}).get('Publication'):

                    try:
                        d = datetime.datetime.today().strptime(
                            trademark_details['PublicationDetails']['Publication']['PublicationDate'],
                            '%d.%m.%Y'
                        )
                    except ValueError:
                        pass
                    else:
                        trademark_details['PublicationDetails']['Publication']['PublicationDate'] = d.strftime('%Y-%m-%d')

                    trademark_details['PublicationDetails'] = [trademark_details['PublicationDetails']['Publication']]
            except AttributeError:
                pass

            if trademark_details.get('PublicationDetails'):
                for x in trademark_details['PublicationDetails']:
                    if len(x.get('PublicationIdentifier')) < 6:
                        x['PublicationIdentifier'] = f"{x['PublicationIdentifier']}/{x['PublicationDate'][:4]}"

            es.index(index=settings.ELASTIC_INDEX_NAME,
                     doc_type='_doc',
                     id=h.meta.id,
                     body=body,
                     request_timeout=30)

        self.stdout.write(self.style.SUCCESS('Finished'))
