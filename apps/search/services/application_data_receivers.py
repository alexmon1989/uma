from typing import List

from apps.search.models import IpcAppList
from apps.search.services.application_raw_data_receivers import (ApplicationRawDataReceiver,
                                                                 ApplicationRawDataFSInvUMLDReceiver,
                                                                 ApplicationRawDataFSInvCertReceiver,
                                                                 ApplicationRawDataFSTMReceiver,
                                                                 ApplicationRawDataFSIDReceiver,
                                                                 ApplicationRawDataFSMadridReceiver,
                                                                 ApplicationRawDataFSGeoReceiver,
                                                                 ApplicationRawDataFSReceiver)
from apps.search.services.application_raw_data_fixers import (ApplicationRawDataFixer,
                                                              ApplicationRawDataFSInvUMLDFixer,
                                                              ApplicationRawDataFSTMFixer,
                                                              ApplicationRawDataFSIDFixer,
                                                              ApplicationRawDataFSMadridFixer,
                                                              ApplicationRawDataFSGeoFixer, ApplicationRawDataFSCRFixer)
from apps.search.services.application_simple_data_creators import (ApplicationSimpleDataCreator,
                                                                   ApplicationSimpleDataInvUMLDCreator,
                                                                   ApplicationSimpleDataInvCertCreator,
                                                                   ApplicationSimpleDataTMCreator,
                                                                   ApplicationSimpleDataIDCreator,
                                                                   ApplicationSimpleDataMadridCreator,
                                                                   ApplicationSimpleDataGeoCreator,
                                                                   ApplicationSimpleDataCRCreator)
from apps.search.services.application_raw_data_filters import (ApplicationRawDataFilter,
                                                               ApplicationRawDataInvUMLDLimitedFilter,
                                                               ApplicationRawDataTMLimitedFilter,
                                                               ApplicationRawDataIDLimitedFilter,
                                                               ApplicationRawDataCRLimitedFilter,
                                                               ApplicationRawDataDecisionLimitedFilter)


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
        self._data_filters = data_filters
        self._simple_search_data_creator = simple_search_data_creator

    def get_data(self) -> dict:
        # Получение данных
        data = self._raw_data_receiver.get_data()

        if data:
            # Исправление данных
            if self._raw_data_fixer:
                self._raw_data_fixer.fix_data(data)

            # Фильтрация данных
            if self._data_filters:
                for _filter in self._data_filters:
                    _filter.filter_data(data)

            # Формирование данных для простого поиска
            data['search_data'] = self._simple_search_data_creator.get_data(self._app, data)

        return data


def create_service(app: IpcAppList, source: str) -> ApplicationGetFullDataService:
    if source == 'filesystem':
        if app.obj_type_id in (1, 2, 3):  # Изобретения, полезные модели, топографии
            raw_data_receiver = ApplicationRawDataFSInvUMLDReceiver(app)
            simple_data_creator = ApplicationSimpleDataInvUMLDCreator()
            raw_data_filters = [ApplicationRawDataInvUMLDLimitedFilter()]
            raw_data_fixer = ApplicationRawDataFSInvUMLDFixer()

            return ApplicationGetFullDataService(
                app,
                raw_data_receiver,
                simple_data_creator,
                raw_data_filters,
                raw_data_fixer
            )
        elif app.obj_type_id == 4:  # ТМ
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
        elif app.obj_type_id == 5:  # ГЗ
            raw_data_receiver = ApplicationRawDataFSGeoReceiver(app)
            simple_data_creator = ApplicationSimpleDataGeoCreator()
            raw_data_fixer = ApplicationRawDataFSGeoFixer()

            return ApplicationGetFullDataService(
                app,
                raw_data_receiver,
                simple_data_creator,
                raw_data_fixer=raw_data_fixer
            )
        elif app.obj_type_id == 6:  # Пром. образцы
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
        elif app.obj_type_id in (9, 14):  # Международные ТМ
            raw_data_receiver = ApplicationRawDataFSMadridReceiver(app)
            simple_data_creator = ApplicationSimpleDataMadridCreator()
            raw_data_fixer = ApplicationRawDataFSMadridFixer()

            return ApplicationGetFullDataService(
                app,
                raw_data_receiver,
                simple_data_creator,
                raw_data_fixer=raw_data_fixer
            )
        elif app.obj_type_id in (10, 13):  # Авт. право
            raw_data_receiver = ApplicationRawDataFSReceiver(app)
            simple_data_creator = ApplicationSimpleDataCRCreator()
            raw_data_filters = [ApplicationRawDataCRLimitedFilter()]
            raw_data_fixer = ApplicationRawDataFSCRFixer()

            return ApplicationGetFullDataService(
                app,
                raw_data_receiver,
                simple_data_creator,
                raw_data_filters,
                raw_data_fixer
            )
        elif app.obj_type_id in (11, 12):  # Договора авт. право
            raw_data_receiver = ApplicationRawDataFSReceiver(app)
            simple_data_creator = ApplicationSimpleDataCRCreator()
            raw_data_filters = [ApplicationRawDataDecisionLimitedFilter()]
            raw_data_fixer = ApplicationRawDataFSCRFixer()

            return ApplicationGetFullDataService(
                app,
                raw_data_receiver,
                simple_data_creator,
                raw_data_filters,
                raw_data_fixer
            )
        elif app.obj_type_id == 16:  # Сертификат доп. охраны
            raw_data_receiver = ApplicationRawDataFSInvCertReceiver(app)
            simple_data_creator = ApplicationSimpleDataInvCertCreator()

            return ApplicationGetFullDataService(
                app,
                raw_data_receiver,
                simple_data_creator
            )
