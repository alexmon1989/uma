import datetime

from django.core.management.base import BaseCommand

from apps.search.services.application_limits import LimitsService, MUC_TO_JSON_CONVERTERS
from apps.search.services.external import CeadLimitsService


class Command(BaseCommand):
    help = 'Imports application limits from EArchive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help=''
        )

    def handle(self, *args, **options):
        cead_limits_service = CeadLimitsService()
        applications = cead_limits_service.get_list(
            datetime_from=datetime.datetime.now() - datetime.timedelta(days=options['days']),
            datetime_to=datetime.datetime.now(),
        )
        exported_count = 0
        for app in applications:
            limits_status, muc_limits = cead_limits_service.get_limit_details(
                app_number=app[0],
                obj_type_id=app[1]
            )
            sis_limits_service = LimitsService(
                app_number=app[0],
                obj_type_id=app[1],
                limits_status=limits_status,
                muc_limits=muc_limits,
                muc_to_json_converter=MUC_TO_JSON_CONVERTERS[app[1]]()
            )
            if sis_limits_service.process():
                exported_count += 1

        self.stdout.write(f'Exported objects count: {exported_count}')
        self.stdout.write('Finished')
