from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from ...models import TransactionType, Transaction, Bulletin
from django.conf import settings
from django.utils import timezone
import json
import datetime


class Command(BaseCommand):
    client = None
    bulletin_date = None
    bulletin = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Bulletin date in format yyyy-mm-dd'
        )

    def fill_tm(self):
        """Заполняет оповещения торговых марок"""
        body = {
            "_source": False,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "Document.idObjType": 4
                            }
                        },
                        {
                            "nested": {
                                "path": "TradeMark.Transactions.Transaction",
                                "query": {
                                    "query_string": {
                                        "query": self.bulletin_date,
                                        "default_field": "TradeMark.Transactions.Transaction.@bulletinDate"
                                    }
                                },
                                "inner_hits": {}
                            }
                        }
                    ]
                }
            }
        }
        s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.client).update_from_dict(body)

        for hit in s.scan():
            for transaction in hit.meta.inner_hits['TradeMark.Transactions.Transaction']:
                transaction_type, created = TransactionType.objects.get_or_create(
                    title=transaction['@name'],
                    obj_type_id=4
                )
                transaction_db = Transaction(
                    bulletin=self.bulletin,
                    transaction_type=transaction_type,
                    json_data=json.dumps(transaction.to_dict()),
                    application_id=hit.meta.id,
                )
                transaction_db.save()

    def fill_id(self):
        """Заполняет оповещения пром. образцов."""
        body = {
            "_source": False,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "Document.idObjType": 6
                            }
                        },
                        {
                            "nested": {
                                "path": "Design.Transactions.Transaction",
                                "query": {
                                    "query_string": {
                                        "query": self.bulletin_date,
                                        "default_field": "Design.Transactions.Transaction.@bulletinDate"
                                    }
                                },
                                "inner_hits": {}
                            }
                        }
                    ]
                }
            }
        }
        s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.client).update_from_dict(body)

        for hit in s.scan():
            for transaction in hit.meta.inner_hits['Design.Transactions.Transaction']:
                transaction_type, created = TransactionType.objects.get_or_create(
                    title=transaction['@name'],
                    obj_type_id=6
                )
                transaction_db = Transaction(
                    bulletin=self.bulletin,
                    transaction_type=transaction_type,
                    json_data=json.dumps(transaction.to_dict()),
                    application_id=hit.meta.id,
                )
                transaction_db.save()

    def fill_inv(self):
        """Заполняет оповещения изобретений"""
        body = {
            "_source": False,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "Document.idObjType": 1
                            }
                        },
                        {
                            "nested": {
                                "path": "TRANSACTIONS.TRANSACTION",
                                "query": {
                                    "query_string": {
                                        "query": self.bulletin_date,
                                        "default_field": "TRANSACTIONS.TRANSACTION.BULLETIN_DATE"
                                    }
                                },
                                "inner_hits": {}
                            }
                        }
                    ]
                }
            }
        }
        s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.client).update_from_dict(body)

        for hit in s.scan():
            for transaction in hit.meta.inner_hits['TRANSACTIONS.TRANSACTION']:
                transaction_type, created = TransactionType.objects.get_or_create(
                    title=transaction['PUBLICATIONNAME'],
                    obj_type_id=1
                )
                transaction_db = Transaction(
                    bulletin=self.bulletin,
                    transaction_type=transaction_type,
                    json_data=json.dumps(transaction.to_dict()),
                    application_id=hit.meta.id,
                )
                transaction_db.save()

    def fill_um(self):
        """Заполняет оповещения полезных моделей."""
        body = {
            "_source": False,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "Document.idObjType": 2
                            }
                        },
                        {
                            "nested": {
                                "path": "TRANSACTIONS.TRANSACTION",
                                "query": {
                                    "query_string": {
                                        "query": self.bulletin_date,
                                        "default_field": "TRANSACTIONS.TRANSACTION.BULLETIN_DATE"
                                    }
                                },
                                "inner_hits": {}
                            }
                        }
                    ]
                }
            }
        }
        s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.client).update_from_dict(body)

        for hit in s.scan():
            for transaction in hit.meta.inner_hits['TRANSACTIONS.TRANSACTION']:
                transaction_type, created = TransactionType.objects.get_or_create(
                    title=transaction['PUBLICATIONNAME'],
                    obj_type_id=2
                )
                transaction_db = Transaction(
                    bulletin=self.bulletin,
                    transaction_type=transaction_type,
                    json_data=json.dumps(transaction.to_dict()),
                    application_id=hit.meta.id,
                )
                transaction_db.save()

    def fill_ld(self):
        """Заполняет оповещения топографий ИМС"""
        body = {
            "_source": False,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "Document.idObjType": 3
                            }
                        },
                        {
                            "nested": {
                                "path": "TRANSACTIONS.TRANSACTION",
                                "query": {
                                    "query_string": {
                                        "query": self.bulletin_date,
                                        "default_field": "TRANSACTIONS.TRANSACTION.BULLETIN_DATE"
                                    }
                                },
                                "inner_hits": {}
                            }
                        }
                    ]
                }
            }
        }
        s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.client).update_from_dict(body)

        for hit in s.scan():
            for transaction in hit.meta.inner_hits['TRANSACTIONS.TRANSACTION']:
                transaction_type, created = TransactionType.objects.get_or_create(
                    title=transaction['PUBLICATIONNAME'],
                    obj_type_id=3
                )
                transaction_db = Transaction(
                    bulletin=self.bulletin,
                    transaction_type=transaction_type,
                    json_data=json.dumps(transaction.to_dict()),
                    application_id=hit.meta.id,
                )
                transaction_db.save()

    def handle(self, *args, **options):
        # Дата бюлетня указывается либо в параметре, либо берётся сегодняшняя
        if options['date']:
            self.bulletin_date = options['date']
        else:
            self.bulletin_date = datetime.datetime.strftime(timezone.now(), '%Y-%m-%d')

        self.client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        try:
            self.bulletin = Bulletin.objects.get(bul_date=datetime.datetime.strptime(self.bulletin_date, '%Y-%m-%d'))
        except Bulletin.DoesNotExist:
            pass
        else:
            # Заполнение БД оповещениями
            self.fill_tm()
            self.fill_id()
            self.fill_inv()
            self.fill_um()
            self.fill_ld()

        self.stdout.write(self.style.SUCCESS('Finished'))
