import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.search.services.application_indexators import ApplicationIndexationService
from apps.search.services.services import application_get_indexed_count
from apps.search.models import IndexationProcess


# Get an instance of a logger
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Клас за допомогою якого відбувається запуск (виклик) команди **search_indexation**.

    Являю собою `Django Management command <https://docs.djangoproject.com/en/dev/howto/custom-management-commands/>`_
    для додавання або оновлення документів у індексі ElasticSearch.

    :cvar help str: Короткий опис команди, який використовується в підказці..
    :cvar indexation_process IndexationProcess: Об'єкт процесу індексації,
     який створюється та оновлюється під час виконання команди.
    """

    help: str = 'Adds or updates documents in ElasticSearch index.'
    indexation_process: IndexationProcess = None

    def add_arguments(self, parser):
        """
        Додає аргументи командного рядка для команди.

        :param parser: Парсер аргументів для додавання параметрів.
        :type parser: argparse.ArgumentParser

        Аргументи:

        - ``--id`` (int): Індексує лише запис з певним ``idAPPNumber`` з таблиці ``IPC_AppLIST``.
        - ``--obj_type`` (int): Додає до індексу лише записи певного типу ОПВ.
        - ``--status`` (int): Додає до індексу лише записи з певним статусом: 1 - заявки, 2 - охоронні документи.
        - ``--ignore_indexed`` (bool): Ігнорує записи з ``elasticindexed=1``.
        """
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
        """
        Основна логіка виконання команди.

        :param args: Додаткові позиційні аргументи.
        :param options: Аргументи командного рядка.

        Логіка:

        - Отримання списку додатків для індексації за допомогою сервісу ``ApplicationIndexationService``.
        - Створення процесу індексації в базі даних.
        - Індексація кожного додатка та оновлення лічильника оброблених записів.
        - Збереження часу завершення індексації та оновлення даних про процес індексації.
        - Виведення повідомлення про успішне завершення процесу індексації.
        """
        apps = ApplicationIndexationService.get_apps_for_indexation(
            ignore_indexed=options['ignore_indexed'],
            app_id=options['id'],
            status=options['status'],
            obj_type=options['obj_type'],
            ignore_apps=[
                'm202006737', 'm202006738', 'm202021203', 'm202021202', 'm202021173', 'm202020602',
                'm202020603', 'm202020601', 'm202020630', 'm202009450', 'm202009453', 'm202009452',
                'a202204078'
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
