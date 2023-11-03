from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from apps.search.models import IpcAppList


class Command(BaseCommand):
    apps = [
        's202101590',
        's202101591',
        's202200041',
        's202200381',
        's202200578',
        's202200634',
        's202200678',
        's202200768',
        's202200786',
        's202200788',
        's202200800',
        's202200801',
        's202200810',
        's202200812',
        's202200825',
        's202200830',
        's202300008',
        's202300012',
        's202300059',
        's202300080',
        's202300092',
        's202300093',
        's202300095',
        's202300098',
        's202300101',
        's202300103',
        's202300104',
        's202300106',
        's202300107',
        's202300108',
        's202300110',
        's202300111',
        's202300112',
        's202300113',
        's202300114',
        's202300115',
        's202300122',
        's202300124',
        's202300128',
        's202300131',
        's202300133',
        's202300136',
        's202300137',
        's202300141',
        's202300143',
        's202300144',
        's202300146',
        's202300147',
        's202300148',
        's202300149',
        's202300151',
        's202300160',
        's202300161',
        's202300163',
        's202300165',
        's202300166',
        's202300167',
        's202300168',
        's202300169',
        's202300170',
        's202300171',
        's202300172',
        's202300175',
        's202300176',
        's202300181',
        's202300189',
        's202300190',
        's202300191',
        's202300193',
        's202300194',
        's202300196',
        's202300197',
        's202300198',
        's202300207',
        's202300210',
        's202300211',
        's202300212',
        's202300213',
        's202300214',
        's202300215',
        's202300216',
        's202300220',
        's202300221',
        's202300225',
        's202300226',
        's202300228',
        's202300233',
        's202300234',
        's202300237',
        's202300238',
        's202300239',
        's202300241',
        's202300244',
        's202300245',
        's202300246',
        's202300247',
        's202300248',
        's202300249',
        's202300251',
        's202300253',
        's202300254',
        's202300255',
        's202300256',
        's202300258',
        's202300259',
        's202300260',
        's202300283',
        's202300284',
        's202300287',
        's202300292',
        's202300293',
        's202300295',
        's202300296',
        's202300297',
        's202300299',
        's202300309',
        's202300310',
        's202300312',
        's202300319',
        's202300322',
        's202300327',
        's202300355',
        's202300359',
        's202300364'
    ]

    ids = []
    app_nums = []

    def get_tm_ids(self):
        for app_number in self.apps:
            apps = IpcAppList.objects.filter(app_number=app_number, obj_type_id=6).order_by('id')
            if not apps[0].registration_number:
                print(apps[0].id)
                self.ids.append(apps[0].id)
                self.app_nums.append(apps[0].app_number)

    def handle(self, *args, **options):
        self.get_tm_ids()



        print(len(self.ids))
        print(self.ids)
        print(self.app_nums)

        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        for _id in self.ids:
            print(f'DELETING {_id}')
            IpcAppList.objects.filter(id=_id).delete()
            q = Q(
                'bool',
                must=[Q('match', _id=_id)],
            )
            s = Search(index=settings.ELASTIC_INDEX_NAME).using(es).query(q)
            s.delete()

        self.stdout.write(self.style.SUCCESS('Finished'))
