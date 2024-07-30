from abc import ABC, abstractmethod
import json
import os
import logging

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from apps.search.models import IpcAppList, AppLimited
from apps.search.mixins import BiblioDataInvUMLDRawGetMixin
from apps.bulletin.services import bulletin_get_number_with_year_by_date
from apps.bulletin.models import EBulletinData


# Get an instance of a logger
logger = logging.getLogger(__name__)


class ApplicationRawDataReceiver(ABC):
    """Абстрактный класс для получения сырых данных заявки."""

    _app: IpcAppList

    def __init__(self, app: IpcAppList):
        self._app = app

    @abstractmethod
    def get_data(self) -> dict:
        pass


class ApplicationRawDataFSReceiver(ApplicationRawDataReceiver):
    """Получает сырые данные заявки с файловой системы."""

    _file_path: str | None = None

    def _set_file_path(self) -> None:
        """Устанавливает путь к файлу JSON с данными объекта."""

        # Если путь к файлу указан сразу (случай с авторским правом)
        if '.json' in self._app.real_files_path:
            self._file_path = self._app.real_files_path
            return

        # Путь к файлу JSON с данными объекта:
        file_name = self._app.registration_number \
            if (self._app.registration_number and self._app.registration_number != '0') \
            else self._app.app_number
        file_name = file_name.replace('/', '_')

        file_path = os.path.join(self._app.real_files_path, f"{file_name}.json")

        # Случай если охранные документы имеют название заявки
        if not os.path.exists(file_path) and self._app.obj_type_id in (4, 5, 6):
            file_name = self._app.app_number.replace('/', '_')
            file_path = os.path.join(self._app.real_files_path, f"{file_name}.json")

        self._file_path = file_path

    def _read_data_from_file(self) -> dict:
        """Читает и возвращает данные из файла."""
        data = {}

        # Чтение содержимого JSON в data
        try:
            f = open(self._file_path, 'r', encoding='utf16')
            try:
                file_content = str.encode(f.read())
                file_content = file_content.replace(b'\xef\xbb\xbf', b'')
                data = json.loads(file_content)
            except json.decoder.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}: {self._file_path}")
        except (UnicodeDecodeError, UnicodeError):
            try:
                f = open(self._file_path, 'r', encoding='utf-8')
                data = json.loads(f.read())
            except json.decoder.JSONDecodeError as e:
                try:
                    f = open(self._file_path, 'r', encoding='utf-8-sig')
                    data = json.loads(f.read())
                except json.decoder.JSONDecodeError as e:
                    logger.error(f"JSONDecodeError: {e}: {self._file_path}")
        except FileNotFoundError as e:
            logger.error(f"JSONDecodeError: {e}")

        return data

    def _set_is_limited(self, data: dict) -> None:
        """Проверяет является ли обїект ограниченной публикацией, устанавливает метку в данных об этом."""
        if data and AppLimited.objects.filter(app_number=self._app.app_number,
                                              obj_type_id=self._app.obj_type_id).exists():
            data['Document']['is_limited'] = True

    def get_data(self) -> dict:
        self._set_file_path()
        data = self._read_data_from_file()

        self._set_is_limited(data)

        return data


class ApplicationRawDataFSTMReceiver(ApplicationRawDataFSReceiver):
    """Получает сырые данные ТМ с файловой системы, получает доп. информацию, которой нет в ФС."""

    def _set_441(self, data: dict) -> None:
        """Устанавливает значение 441-го поля, если оно отсутствует в данных."""
        if data and not data['TradeMark']['TrademarkDetails'].get('Code_441'):
            bulletin_item = EBulletinData.objects.filter(
                app_number=data['TradeMark']['TrademarkDetails'].get('ApplicationNumber')
            ).first()
            if bulletin_item:
                data['TradeMark']['TrademarkDetails']['Code_441'] = bulletin_item.publication_date.strftime('%Y-%m-%d')

    def get_data(self) -> dict:
        data = super().get_data()

        self._set_441(data)

        return data


class ApplicationRawDataFSIDReceiver(ApplicationRawDataFSReceiver):
    """Получает сырые данные пром. образца с файловой системы, получает доп. информацию, которой нет в ФС."""
    pass


class ApplicationRawDataFSInvUMLDReceiver(ApplicationRawDataFSReceiver, BiblioDataInvUMLDRawGetMixin):
    """Получает сырые данные изобретения, полезной модели, топографии с файловой системы,
    получает доп. информацию, которой нет в ФС."""

    def _set_i_43_bul_str(self, biblio_data: dict) -> None:
        if biblio_data.get('I_43.D'):
            i_43_d = biblio_data['I_43.D'][0]
            bull_str = bulletin_get_number_with_year_by_date(i_43_d)
            if bull_str:
                biblio_data['I_43_bul_str'] = bull_str

    def _set_i_45_bul_str(self, biblio_data: dict) -> None:
        if biblio_data.get('I_45.D'):
            i_45_d = biblio_data['I_45.D'][len(biblio_data['I_45.D']) - 1]
            bull_str = bulletin_get_number_with_year_by_date(i_45_d)
            if bull_str:
                biblio_data['I_45_bul_str'] = bull_str

    def get_data(self) -> dict:
        data = super().get_data()

        biblio_data = self.get_biblio_data(data)
        self._set_i_43_bul_str(biblio_data)
        self._set_i_45_bul_str(biblio_data)

        return data


class ApplicationRawDataFSInvCertReceiver(ApplicationRawDataFSReceiver):
    pass


class ApplicationRawDataFSMadridReceiver(ApplicationRawDataFSReceiver):
    """Получает сырые данные международных ТМ, получает доп. информацию, которой нет в ФС."""
    def _set_441(self, data: dict) -> None:
        try:
            app = IpcAppList.objects.filter(
                obj_type_id=9,  # registration_date у заявки с этим obj_type_id и будет 441-м кодом
                app_number=self._app.app_number
            ).first()
            data['MadridTradeMark']['TradeMarkDetails']['Code_441'] = app.registration_date.strftime('%Y-%m-%d')
        except AttributeError:
            data['MadridTradeMark']['TradeMarkDetails']['Code_441'] = self._app.registration_date.strftime('%Y-%m-%d')

    def get_data(self) -> dict:
        data_from_file = super().get_data()

        data = {
            'Document': {
                'idObjType': self._app.obj_type_id,
                'filesPath': self._app.files_path
            },
            'MadridTradeMark': {
                'TradeMarkDetails': data_from_file
            }
        }

        self._set_441(data)

        return data


class ApplicationRawDataFSMadrid9Receiver(ApplicationRawDataFSMadridReceiver):
    """Получает сырые данные международных ТМ с распространением на территорию Украины,
    получает доп. информацию, которой нет в ФС."""

    def _set_450(self, data: dict) -> None:
        """Если это "Міжнародна реєстрація торговельної марки з поширенням на територію України",
        то надо проверить есть ли аналогичная "Міжнародна реєстрація торговельної марки, що зареєстрована в Україні"
        и взять у неё 450 код."
        """
        es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        q = Q(
            'bool',
            must=[
                Q('match', Document__idObjType=14),
                Q('match', search_data__protective_doc_number=self._app.registration_number),
            ],
        )
        s = Search(index=settings.ELASTIC_INDEX_NAME).using(es).query(q).execute()
        if s:
            hit = s[0].to_dict()
            data['MadridTradeMark']['TradeMarkDetails']['ENN'] = hit['MadridTradeMark']['TradeMarkDetails']['ENN']

    def get_data(self) -> dict:
        data = super().get_data()

        self._set_450(data)

        return data


class ApplicationRawDataFSGeoReceiver(ApplicationRawDataFSReceiver):
    """Получает сырые данные ГЗ,
    получает доп. информацию, которой нет в ФС."""
    pass
