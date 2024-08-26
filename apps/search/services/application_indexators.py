from django.db.models import QuerySet, Q
from django.utils import timezone

from typing import List

from apps.search.models import IpcAppList
from apps.search.services.application_data_receivers import create_service as create_data_receiver_service
from apps.search.services.application_data_writers import create_service as create_data_writer_service


class ApplicationIndexationService:
    """Сервіс для додавання інформації про заявку в пошуковий індекс."""

    @staticmethod
    def get_apps_for_indexation(
            ignore_indexed: bool = False,
            app_id: int | None = None,
            obj_type: int | None = None,
            status: int | None = None,
            ignore_apps: List[str] = None
    ) -> QuerySet[IpcAppList]:
        """
        Повертає список заявок, які необхідно додати в пошуковий індекс.

        :param ignore_indexed: Якщо встановлено в `True`, ігнорує заявки, які вже індексовані.
        :type ignore_indexed: bool, optional
        :param app_id: Ідентифікатор заявки для індексації. Якщо вказано, індексується тільки одна заявка.
        :type app_id: int, optional
        :param obj_type: Тип об'єкта для фільтрації заявок.
        :type obj_type: int, optional
        :param status: Статус заявки для фільтрації: 1 - заявки, 2 - охоронні документи.
        :type status: int, optional
        :param ignore_apps: Список номерів заявок, які потрібно ігнорувати під час індексації.
        :type ignore_apps: List[str], optional

        :return: QuerySet з заявками, які потрібно додати в індекс.
        :rtype: QuerySet[apps.search.models.IpcAppList]
        """
        if not ignore_apps:
            ignore_apps = []

        apps = IpcAppList.objects.exclude(
            Q(registration_date__gte=timezone.now()) | Q(app_number__in=ignore_apps)
        )

        # Фильтрация по параметрам командной строки
        if not ignore_indexed:
            apps = apps.filter(elasticindexed=0)
        if app_id:
            apps = apps.filter(id=app_id)
        if obj_type:
            apps = apps.filter(obj_type=obj_type)
        if status:
            status = int(status)
            if status == 1:
                apps = apps.filter(registration_number__isnull=True)
            elif status == 2:
                apps = apps.exclude(registration_number__isnull=True)

        return apps

    @staticmethod
    def index_application(app: IpcAppList) -> bool:
        """
        Індексує дані заявки.

        :param app: Об'єкт заявки для індексації.
        :type app: apps.search.models.IpcAppList

        :return: Успішність індексації.
        :rtype: bool
        """

        # Получение данных
        data_receiver_service = create_data_receiver_service(app, 'filesystem')
        data = data_receiver_service.get_data()

        # Запись данных
        if data:
            data_writer_service = create_data_writer_service(app, data)
            data_writer_service.write()
            return True

        return False
