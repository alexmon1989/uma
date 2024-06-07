from abc import abstractmethod, ABC

from django.conf import settings

from apps.search.models import IpcAppList


class ApplicationRawDataReceiver(ABC):
    _app: IpcAppList

    def __init__(self, app: IpcAppList):
        self._app = app

    @abstractmethod
    def get_data(self) -> dict:
        pass


class ApplicationRawDataTMReceiver(ApplicationRawDataReceiver):
    pass


class ApplicationRawDataFixer(ABC):
    @abstractmethod
    def fix_data(self, data: dict):
        pass


class ApplicationRawDataTMFixer(ApplicationRawDataFixer):
    pass


class ApplicationSimpleDataCreator(ABC):

    @abstractmethod
    def get_data(self, data: dict) -> dict:
        pass


class ApplicationSimpleDataTMCreator(ApplicationSimpleDataCreator):
    pass


SERVICE_CONFIG = {
    'filesystem': {
        'raw_data_receivers': {
            4: ApplicationRawDataTMReceiver
        },
        'raw_data_fixers': {
            4: ApplicationRawDataTMFixer
        },
        'simple_search_data_creators': {
            4: ApplicationSimpleDataTMCreator
        }
    }
}


class ApplicationGetFullDataFSService:
    """Сервис позволяет получить полные сырые данные заявки."""
    _raw_data_receiver: ApplicationRawDataReceiver
    _raw_data_fixer: ApplicationRawDataFixer | None = None
    _simple_search_data_creator: ApplicationSimpleDataCreator

    def __init__(self, app: IpcAppList):
        self._app: IpcAppList = app

        # Создание объектов для получения информации о заявке
        self._raw_data_receiver = \
            SERVICE_CONFIG[settings.APPLICATIONS_DATA_SOURCE]['raw_data_receivers'][self._app.obj_type_id](self._app)
        self._raw_data_fixer = \
            SERVICE_CONFIG[settings.APPLICATIONS_DATA_SOURCE]['raw_data_fixers'][self._app.obj_type_id]()
        self._simple_search_data_creator = \
            SERVICE_CONFIG[settings.APPLICATIONS_DATA_SOURCE]['simple_search_data_creators'][self._app.obj_type_id]()

    def get_data(self) -> dict:
        data = self._raw_data_receiver.get_data()

        if self._raw_data_fixer:
            self._raw_data_fixer.fix_data(data)

        data['search_data'] = self._simple_search_data_creator.get_data(data)

        return data
