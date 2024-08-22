import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.search.services.application_indexators import ApplicationIndexationService
from apps.search.services.services import application_get_indexed_count
from apps.search.models import IndexationProcess


# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help: str = 'Adds or updates documents in ElasticSearch index.'
    indexation_process: IndexationProcess = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            help='Index only one record with certain idAPPNumber from table IPC_AppLIST'
        )
        parser.add_argument(
            '--obj_type',
            type=int,
            help='Add to index only records with certain object type.'
        )
        parser.add_argument(
            '--status',
            type=int,
            help='Add to index only records with certain status: 1 - applications, 2 - protective documents.'
        )
        parser.add_argument(
            '--ignore_indexed',
            type=bool,
            help='Ignores elasticindexed=1'
        )

    def handle(self, *args, **options):
        apps = ApplicationIndexationService.get_apps_for_indexation(
            ignore_indexed=options['ignore_indexed'],
            app_id=options['id'],
            status=options['status'],
            obj_type=options['obj_type'],
            ignore_apps=[
                'm202006737', 'm202006738', 'm202021203', 'm202021202', 'm202021173', 'm202020602',
                'm202020603', 'm202020601', 'm202020630', 'm202009450', 'm202009453', 'm202009452'
            ]
        )

        self.stdout.write(self.style.SUCCESS(
            f'The list of documents has been successfully received ({apps.count()} items).'
        ))

        # Создание процесса индексации в БД
        self.indexation_process = IndexationProcess.objects.create(
            begin_date=timezone.now(),
            not_indexed_count=apps.count()
        )

        for app in apps:
            ApplicationIndexationService.index_application(app)
            self.indexation_process.processed_count += 1
            self.indexation_process.save()

        # Время окончания процесса индексации и сохранение данных процесса индексации
        self.indexation_process.finish_date = timezone.now()
        self.indexation_process.documents_in_index = application_get_indexed_count()
        self.indexation_process.save()

        self.stdout.write(self.style.SUCCESS('Finished'))
