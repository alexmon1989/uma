from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from apps.bulletin.models import ClListOfficialBulletinsIp


class Command(BaseCommand):
    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        # Заявки на изобретения, у которых есть I_43.D
        query = Q(
            "match",
            Document__idObjType=1,
        ) & ~Q(
            'query_string',
            query="_exists_:Claim.I_11"
        ) & Q(
            'query_string',
            query="_exists_:Claim.I_43.D AND NOT _exists_:Claim.I_43_bul_str"
        )
        s = Search().using(es).query(query)
        c = s.count()
        i = 0
        for h in s.scan():
            body = h.to_dict()

            i += 1
            print(f"apps: {i}/{c} - {body['Claim']['I_21']} - {h.meta.id}")

            i_43_d = body['Claim']['I_43.D'][0]
            bulletin = ClListOfficialBulletinsIp.objects.get(bul_date=i_43_d)
            bull_str = f"{bulletin.bul_number}/{bulletin.bul_date.year}"
            body['Claim']['I_43_bul_str'] = bull_str
            es.index(index=settings.ELASTIC_INDEX_NAME,
                     doc_type='_doc',
                     id=h.meta.id,
                     body=body,
                     request_timeout=30)

        # Патенты на изобретения, полезные модели, у которых есть I_45.D
        query = Q(
            'query_string',
            query="_exists_:Patent.I_45.D AND NOT _exists_:Patent.I_45_bul_str"
        )
        s = Search().using(es).query(query)
        c = s.count()
        i = 0
        for h in s.scan():
            body = h.to_dict()

            i += 1
            print(f"pr. docs: {i}/{c} - {body['Patent']['I_21']} - {h.meta.id}")

            i_45_d = body['Patent']['I_45.D'][len(body['Patent']['I_45.D'])-1]
            bulletin = ClListOfficialBulletinsIp.objects.get(bul_date=i_45_d)
            bull_str = f"{bulletin.bul_number}/{bulletin.bul_date.year}"
            body['Patent']['I_45_bul_str'] = bull_str
            es.index(index=settings.ELASTIC_INDEX_NAME,
                     doc_type='_doc',
                     id=h.meta.id,
                     body=body,
                     request_timeout=30)

        self.stdout.write(self.style.SUCCESS('Finished'))
