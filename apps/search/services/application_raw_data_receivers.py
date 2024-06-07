from abc import ABC, abstractmethod
import json
import os
import logging

from apps.search.models import IpcAppList


# Get an instance of a logger
logger = logging.getLogger(__name__)


class ApplicationRawDataReceiverService(ABC):
    @abstractmethod
    def get_data(self, app: IpcAppList) -> dict:
        pass


class ApplicationRawDataReceiverFilesystemService(ApplicationRawDataReceiverService):

    app: IpcAppList
    _file_path: str

    def _set_file_path(self) -> None:
        """Получает путь к файлу JSON с данными объекта."""

        # Если путь к файлу указан сразу (случай с авторским правом)
        if '.json' in self.app.real_files_path:
            self._file_path = self.app.real_files_path

        # Путь к файлу JSON с данными объекта:
        file_name = self.app.registration_number \
            if (self.app.registration_number and self.app.registration_number != '0') \
            else self.app.app_number
        file_name = file_name.replace('/', '_')

        file_path = os.path.join(self.app.real_files_path, f"{file_name}.json")

        # Случай если охранные документы имеют название заявки
        if not os.path.exists(file_path) and self.app.obj_type_id in (4, 5, 6):
            file_name = self.app.app_number.replace('/', '_')
            file_path = os.path.join(self.app.real_files_path, f"{file_name}.json")

        self._file_path = file_path

    def _read_data_from_file(self) -> dict:
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
            logger.error(f"JSONDecodeError: {e}: {self._file_path}")

        return data

    def get_data(self, app: IpcAppList) -> dict:
        self.app = app
        self._set_file_path()
        data = self._read_data_from_file()

        # Получение доп. данных, которые отсутствуют в источнике

        return data
