from typing import List

from apps.search.models import IpcAppList
from apps.search.services.application_raw_data_receivers import (ApplicationRawDataReceiver,
                                                                 ApplicationRawDataFSTMReceiver,
                                                                 ApplicationRawDataFSIDReceiver)
from apps.search.services.application_raw_data_fixers import (ApplicationRawDataFixer,
                                                              ApplicationRawDataFSTMFixer,
                                                              ApplicationRawDataFSIDFixer)
from apps.search.services.application_simple_data_creators import (ApplicationSimpleDataCreator,
                                                                   ApplicationSimpleDataTMCreator,
                                                                   ApplicationSimpleDataIDCreator)
from apps.search.services.application_raw_data_filters import (ApplicationRawDataFilter,
                                                               ApplicationRawDataTMLimitedFilter,
                                                               ApplicationRawDataIDLimitedFilter)


class ApplicationGetFullDataService:
    """Сервис позволяет получить полные сырые данные заявки."""
    _raw_data_receiver: ApplicationRawDataReceiver
    _raw_data_fixer: ApplicationRawDataFixer | None = None
    _simple_search_data_creator: ApplicationSimpleDataCreator
    _data_filters: List[ApplicationRawDataFilter]
    _app: IpcAppList

    def __init__(self,
                 app: IpcAppList,
                 raw_data_receiver: ApplicationRawDataReceiver,
                 simple_search_data_creator: ApplicationSimpleDataCreator,
                 data_filters: List[ApplicationRawDataFilter] = None,
                 raw_data_fixer: ApplicationRawDataFixer | None = None):
        self._app = app
        self._raw_data_receiver = raw_data_receiver
        self._raw_data_fixer = raw_data_fixer
        self.data_filters = data_filters
        self._simple_search_data_creator = simple_search_data_creator

    def get_data(self) -> dict:
        # Получение данных
        data = self._raw_data_receiver.get_data()

        if data:
            # Исправление данных
            if self._raw_data_fixer:
                self._raw_data_fixer.fix_data(data)

            # Фильтрация данных
            if self.data_filters:
                for _filter in self.data_filters:
                    _filter.filter_data(data)

            # Формирование данных для простого поиска
            data['search_data'] = self._simple_search_data_creator.get_data(self._app, data)

        return data


def create_service(app: IpcAppList, source: str) -> ApplicationGetFullDataService:
    if source == 'filesystem':
        if app.obj_type_id == 4:
            raw_data_receiver = ApplicationRawDataFSTMReceiver(app)
            simple_data_creator = ApplicationSimpleDataTMCreator()
            raw_data_filters = [ApplicationRawDataTMLimitedFilter()]
            raw_data_fixer = ApplicationRawDataFSTMFixer()

            return ApplicationGetFullDataService(
                app,
                raw_data_receiver,
                simple_data_creator,
                raw_data_filters,
                raw_data_fixer
            )
        elif app.obj_type_id == 6:
            raw_data_receiver = ApplicationRawDataFSIDReceiver(app)
            simple_data_creator = ApplicationSimpleDataIDCreator()
            raw_data_filters = [ApplicationRawDataIDLimitedFilter()]
            raw_data_fixer = ApplicationRawDataFSIDFixer()

            return ApplicationGetFullDataService(
                app,
                raw_data_receiver,
                simple_data_creator,
                raw_data_filters,
                raw_data_fixer
            )
