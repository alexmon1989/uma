from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


class Command(BaseCommand):
    source_host = '10.11.11.51:9200'
    source_index = 'uma2'
    dest_host = '10.11.11.51:9200'
    dest_index = 'uma3'

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es_source = Elasticsearch(self.source_host, timeout=settings.ELASTIC_TIMEOUT)
        es_dest = Elasticsearch(self.dest_host, timeout=settings.ELASTIC_TIMEOUT)

        error_ids = []
        query = Q(
            "query_string",
            # query="search_data.app_date:{2020-01-01 TO *}'"
            query="*"
        )
        s = Search(index=self.source_index).using(es_source).query(query)
        c = s.count()
        i = 0

        for h in s.params(size=10).scan():
            i += 1
            print(f"{i}/{c} - {h.meta.id}")

            # Поиск в индексе назначения
            dest_app = Search(using=es_dest, index=self.dest_index).query("match", _id=h.meta.id).execute()
            if not dest_app:
                body = h.to_dict()

                # Преобразование search_data
                for t in ('agent', 'applicant', 'inventor', 'owner'):
                    if body['search_data'].get(t):
                        items = []
                        for item in body['search_data'][t]:
                            items.append(
                                {
                                    'name': item
                                }
                            )
                        body['search_data'][t] = items

                # Fix CorrespondenceAddress
                if body.get('TradeMark', {}).get('TrademarkDetails', {}).get('CorrespondenceAddress', {}):
                    if not body['TradeMark']['TrademarkDetails']['CorrespondenceAddress'].get('CorrespondenceAddressBook'):
                        body['TradeMark']['TrademarkDetails']['CorrespondenceAddress']['CorrespondenceAddressBook'] = \
                        body['TradeMark']['TrademarkDetails']['CorrespondenceAddress']
                if body.get('Design', {}).get('DesignDetails', {}).get('CorrespondenceAddress', {}):
                    if not body['Design']['DesignDetails']['CorrespondenceAddress'].get('CorrespondenceAddressBook'):
                        body['Design']['DesignDetails']['CorrespondenceAddress']['CorrespondenceAddressBook'] = \
                        body['Design']['DesignDetails']['CorrespondenceAddress']

                try:
                    es_dest.index(index=self.dest_index,
                                  doc_type='_doc',
                                  id=h.meta.id,
                                  body=body,
                                  request_timeout=30)
                except:
                    error_ids.append(h.meta.id)
        print(error_ids)
