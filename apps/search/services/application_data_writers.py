from abc import ABC, abstractmethod
import logging
import datetime
import os
import shutil

from django.db import transaction
from django.conf import settings

from elasticsearch import Elasticsearch, exceptions as elasticsearch_exceptions

from apps.search.models import IpcAppList
from apps.bulletin.models import EBulletinData


# Get an instance of a logger
logger = logging.getLogger(__name__)


class ApplicationWriter(ABC):
    _app: IpcAppList
    _app_data: dict

    def __init__(self, app: IpcAppList, app_data: dict):
        self._app = app
        self._app_data = app_data

    @abstractmethod
    def write(self):
        pass


class ApplicationESWriter(ApplicationWriter):
    """Пишет данные в индекс ElasticSearch, обновляет данные об индексации в БД."""
    def __init__(self, app: IpcAppList, app_data: dict):
        super().__init__(app, app_data)

        # Клиент ElasticSearch
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

    def _write_es(self) -> bool:
        """Записывает данные в ES."""
        try:
            self.es.index(
                index=settings.ELASTIC_INDEX_NAME,
                doc_type='_doc',
                id=self._app.id,
                body=self._app_data,
                request_timeout=30
            )
        except elasticsearch_exceptions.RequestError as e:
            logger.error(f"ElasticSearch RequestError: {e}: id={self._app.pk}")
        except elasticsearch_exceptions.ConnectionTimeout as e:
            logger.error(f"ElasticSearch ConnectionTimeout: {e}: id={self._app.pk}")
        else:
            return True
        return False

    def _update_db_data(self):
        """Обновляет данные в БД."""
        self._app.last_indexation_date = datetime.datetime.now()
        self._app.elasticindexed = 1
        self._app.save()

    def write(self):
        if self._write_es():
            self._update_db_data()


class ApplicationESTMWriter(ApplicationESWriter):
    """Пишет данные ТМ в индекс ElasticSearch, обновляет данные об индексации в БД, обновляет другую информацию.."""

    def _should_be_censored(self) -> bool:
        """Проверяет, содержит ли изображение ТМ запрещённые элементы."""
        censored_notices_types_list = (
            'CONTAINS_OBSCENE_WORDS_AND_EXPRESSIONS',  # Містить нецензурні слова та вислови
            'CONTAINS_PORNOGRAFIC_IMAGES',  # 'Містить порнографічні зображення',
            'CONTAINS_PROPAGANDA_OF_NATIONAL_ENMITY',  # 'Містить пропагування національної ворожнечі',
            'CONTAINS_PROPAGANDA_OF_RELIGIOUS_ENMITY',  # 'Містить пропагування релігійної ворожнечі',
            'CONTAINS_THE_PROMOTION_OF_FASCISM_AND_NEOFASHISM',  # 'Містить пропагування фашизму та неофашизму'
        )
        notice_type = self._app_data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage'].get(
            'MarkImageTypeNotice'
        )
        return notice_type and notice_type in censored_notices_types_list

    def _censor_image(self):
        """Подменяет файл с изображением на изображение-заглушку."""
        if self._should_be_censored():
            image_name_json = self._app_data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage'][
                'MarkImageFilename']
            image_json_path = os.path.join(self._app.real_files_path, image_name_json)
            censored_image_path = os.path.join(settings.BASE_DIR, 'assets', 'img', 'censored.jpg')
            shutil.copyfile(censored_image_path, image_json_path)

    def _write_441(self):
        if self._app_data['TradeMark']['TrademarkDetails'].get('Code_441'):
            EBulletinData.objects.update_or_create(
                app_number=self._app_data['TradeMark']['TrademarkDetails'].get('ApplicationNumber'),
                unit_id=1,
                defaults={
                    'publication_date': datetime.datetime.strptime(
                        self._app_data['TradeMark']['TrademarkDetails']['Code_441'],
                        '%Y-%m-%d'
                    )
                }
            )

    def write(self):
        super().write()
        self._write_441()
        self._censor_image()


class ApplicationWriteIndexationService:
    """Сервис для записи информации о заявке в поисковый индекс."""
    _writer: ApplicationWriter

    def __init__(self, writer: ApplicationWriter):
        self._writer = writer

    def write(self):
        with transaction.atomic():
            self._writer.write()


def create_service(app: IpcAppList, app_data: dict):
    if app.obj_type_id == 4:
        writer = ApplicationESTMWriter(app, app_data)
        return ApplicationWriteIndexationService(writer)
