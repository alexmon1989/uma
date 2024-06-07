from abc import ABC, abstractmethod
import datetime

from elasticsearch import Elasticsearch
from django.conf import settings

from apps.search.models import IpcAppList
from apps.search.services.application_raw_data_receivers import (ApplicationRawDataReceiverService,
                                                                 ApplicationRawDataReceiverFilesystemService)
from apps.search.services.application_raw_data_fixers import (ApplicationRawDataFixerService,
                                                              ApplicationRawDataFixerFSService)
from apps.search.services.application_simple_data_creators import ApplicationSimpleDataCreatorService


class ApplicationIndexationValidator(ABC):
    """Валидирует данные заявки. Проверяет пригодны ли данные для записи в поисковый индекс."""
    def __init__(self, app_data: dict):
        self._app_data = app_data

    @abstractmethod
    def is_valid(self) -> bool:
        pass


class ApplicationIndexationValidatorTM(ApplicationIndexationValidator):
    """Валидирует данные ТМ."""

    def is_valid(self) -> bool:
        today = datetime.datetime.now()

        publication = self._app_data.get('TradeMark', {}).get('TrademarkDetails', {}).get('PublicationDetails', [])
        for item in publication:
            if datetime.datetime.strptime(item['PublicationDate'], '%Y-%m-%d') > today:
                return False

        transactions = self._app_data.get('TradeMark', {}).get('Transactions', {}).get('Transaction', [])
        for item in transactions:
            if datetime.datetime.strptime(item['@bulletinDate'], '%Y-%m-%d') > today:
                return False

        return True


class ApplicationIndexationValidatorService:
    """Производит валидацию данных заявки. Проверяет пригодны ли данные для записи в поисковый индекс."""
    def is_valid(self, app_data: dict):
        if app_data['Document']['idObjType'] == 4:
            validator = ApplicationIndexationValidatorTM(app_data)
            return validator.is_valid()
        return True


class ApplicationIndexationService:
    """Класс для добавления информации о заявке в поисковый индекс."""

    _app: IpcAppList
    _index_data: dict | None = None
    _app_data_receiver: ApplicationRawDataReceiverService
    _app_simple_data_creator: ApplicationSimpleDataCreatorService
    _app_data_fixer: ApplicationRawDataFixerService
    _validator: ApplicationIndexationValidatorService

    def __init__(self):
        if settings.APP_DATA_SOURCE == 'filesystem':
            self._app_data_receiver = ApplicationRawDataReceiverFilesystemService()
            self._app_simple_data_creator = ApplicationSimpleDataCreatorService()
            self._app_data_fixer = ApplicationRawDataFixerFSService()
            self._validator = ApplicationIndexationValidatorService()

    def _receive_raw_data(self):
        """Получает "сырые" данные заявки."""
        self._index_data = self._app_data_receiver.get_data(self._app)

    def _make_simple_search_data(self):
        """Создаёт и заполняет self._index_data['search_data'] (данные для "простого поиска")."""
        self._index_data['search_data'] = self._app_simple_data_creator.get_simple_search_data(self._index_data)

    def _prepare_index_data(self):
        self._make_simple_search_data()
        # Фильтрация данных

    def _write_data(self):
        """Записывает данные в поисковый индекс, БД, диск (цензор изображений)"""
        # self.ApplicationDataWriter.write()

        # Инициализация клиента ElasticSearch
        self._es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

    def process(self, app: IpcAppList) -> None:
        self._app = app
        self._index_data = None

        # Получение данных из файла
        self._receive_raw_data()

        if self._index_data:
            # Исправление данных
            if self._app_data_fixer:
                self._app_data_fixer.fix_data(self._index_data)

            # Подготовка данных для помещения в индекс
            self._prepare_index_data()

            # Помещение данных в индекс
            if self._validator.is_valid(self._index_data):
                self._write_data()
