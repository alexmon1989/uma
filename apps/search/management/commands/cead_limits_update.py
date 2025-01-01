import datetime
from typing import Tuple

from django.core.management.base import BaseCommand

from apps.search.services.application_limits import LimitsService, MUC_TO_DICT_CONVERTERS
from apps.search.services.external import CeadLimitsService


class Command(BaseCommand):
    cead_limits_service: CeadLimitsService = None
    help = 'Imports application limits from EArchive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Number of elapsed days for which data will be exported'
        )

    def _process_application(self, app: Tuple[str, int]) -> bool:
        """Обробляє одну заявку."""
        limits_status, muc_limits = self.cead_limits_service.get_limit_details(
            app_number=app[0],
            obj_type_id=app[1]
        )
        muc_to_json_converter = MUC_TO_DICT_CONVERTERS[app[1]]()

        sis_limits_service = LimitsService(
            app_number=app[0],
            obj_type_id=app[1],
            limits_status=limits_status,
            limits=muc_to_json_converter.convert()
        )
        return sis_limits_service.process()

    def handle(self, *args, **options):
        self.cead_limits_service = CeadLimitsService()

        # Отримання списку заявок з обмеженнями
        applications = self.cead_limits_service.get_list(
            datetime_from=datetime.datetime.now() - datetime.timedelta(days=options['days']),
            datetime_to=datetime.datetime.now(),
        )
        exported_count = 0
        for app in applications:
            # Обробка заявки
            if self._process_application(app):
                exported_count += 1

        self.stdout.write(f'Exported objects count: {exported_count}')
        self.stdout.write('Finished')
