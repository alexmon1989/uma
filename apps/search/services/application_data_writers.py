from abc import ABC, abstractmethod
import logging
import datetime
import os
import shutil

from django.db import transaction
from django.conf import settings

from elasticsearch import Elasticsearch, exceptions as elasticsearch_exceptions
from elasticsearch_dsl import Search, Q

from apps.search.mixins import BiblioDataInvUMLDRawGetMixin
from apps.search.models import IpcAppList, AppDocuments, AppLimited
from apps.search.utils import delete_files_in_directory
from apps.search.services.application_indexation_validators import (ApplicationIndexationValidator,
                                                                    ApplicationIndexationInvUMLDValidator,
                                                                    ApplicationIndexationIDValidator,
                                                                    ApplicationIndexationTMValidator)
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
        self._app.open_data_updated = 0
        self._app.is_limited = self._app_data.get('Document', {}).get('is_limited', 0)
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


class ApplicationESIDWriter(ApplicationESWriter):
    """Пишет данные пром. образца в индекс ElasticSearch, обновляет данные об индексации в БД,
    обновляет другую информацию."""
    def _delete_limited_images(self):
        if self._app_data['Document'].get('is_limited'):
            # Удаление всех .jpeg, .jpg, .png, .tiff из каталога
            exts = ['.jpeg', '.jpg', '.png', '.tiff']
            exts_upper = list(map(lambda x: x.upper(), exts))
            for ext in (exts + exts_upper):
                delete_files_in_directory(self._app.real_files_path, ext)

    def write(self):
        super().write()
        self._delete_limited_images()


class ApplicationESInvUMLDWriter(ApplicationESWriter, BiblioDataInvUMLDRawGetMixin):
    """Пишет данные изобретения, полезной модели, топографии в индекс ElasticSearch,
    обновляет данные об индексации в БД,
    обновляет другую информацию."""

    def _delete_limited_files(self):
        """Удаляет файлы документов с диска."""
        if self._app_data['Document'].get('is_limited'):
            biblio_data = self.get_biblio_data(self._app_data)

            limited_app = AppLimited.objects.filter(
                app_number=biblio_data['I_21'],
                obj_type_id=self._app_data['Document']['idObjType']
            ).first()

            documents = AppDocuments.objects.filter(app=self._app)

            if not limited_app.settings_dict.get('AB', False):
                for doc in documents:
                    if doc.enter_num == 100 and os.path.exists(doc.real_file_path):
                        os.remove(doc.real_file_path)
            if not limited_app.settings_dict.get('CL', False):
                for doc in documents:
                    if doc.enter_num == 98 and doc.file_type == 'pdf' and os.path.exists(doc.real_file_path):
                        os.remove(doc.real_file_path)
            if not limited_app.settings_dict.get('DE', False):
                for doc in documents:
                    if doc.enter_num in (99, 101) and os.path.exists(doc.real_file_path):
                        os.remove(doc.real_file_path)

    def _update_notification_date(self):
        """Обновляет notification_date - дату последнего оповещения по охранному документу в бюллетене."""
        if 'TRANSACTIONS' in self._app_data:
            # Самая свежая дата оповещения
            notification_date = max(
                item['BULLETIN_DATE'] for item in self._app_data['TRANSACTIONS']['TRANSACTION']
                if 'BULLETIN_DATE' in item
            )
            self._app.notification_date = notification_date
            self._app.save()

    def write(self):
        super().write()
        self._update_notification_date()
        self._delete_limited_files()


class ApplicationESInvCertWriter(ApplicationESWriter):
    """Пишет данные сертификата дополнительной охраны в индекс ElasticSearch,
    обновляет данные об индексации в БД,
    обновляет другую информацию."""
    pass


class ApplicationESMadridWriter(ApplicationESWriter):
    """Пишет данные международной ТМ в индекс ElasticSearch, данные об индексации в БД, другую информацию."""

    def _write_450(self):
        """Если это "Міжнародна реєстрація торговельної марки, що зареєстрована в Україні", которая появляется
        позже чем "Міжнародна реєстрація торговельної марки з поширенням на територію України" с тем же номером,
        то необхожимо обновить 450-й код у "Міжнародна реєстрація торговельної марки з поширенням на територію України"
        """
        if self._app.obj_type_id == 14:
            q = Q(
                'bool',
                must=[
                    Q('match', Document__idObjType=9),
                    Q('match', search_data__protective_doc_number=self._app.registration_number),
                ],
            )
            s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.es).query(q).execute()
            if s:
                hit = s[0].to_dict()
                hit['MadridTradeMark']['TradeMarkDetails']['ENN'] = self._app_data['MadridTradeMark']['TradeMarkDetails']['ENN']
                self.es.index(index=settings.ELASTIC_INDEX_NAME,
                              doc_type='_doc',
                              id=s[0].meta.id,
                              body=hit,
                              request_timeout=30)

    def _write_441(self) -> None:
        """Запись в БД для бюлетня."""
        EBulletinData.objects.update_or_create(
            app_number=self._app.registration_number,
            unit_id=2,
            defaults={'publication_date': self._app_data['MadridTradeMark']['TradeMarkDetails']['Code_441']}
        )

    def write(self):
        super().write()
        self._write_450()
        self._write_441()


class ApplicationESGeoWriter(ApplicationESWriter):
    """Пишет данные ГЗ в индекс ElasticSearch, данные об индексации в БД, другую информацию."""

    def _write_441(self) -> None:
        """Запись в БД для бюлетеня."""
        if 'ApplicationPublicationDetails' in self._app_data['Geo']['GeoDetails']:
            EBulletinData.objects.update_or_create(
                app_number=self._app_data['Geo']['GeoDetails'].get('ApplicationNumber'),
                unit_id=3,
                defaults={
                    'publication_date': self._app_data['Geo']['GeoDetails']['ApplicationPublicationDetails'][
                        'PublicationDate']
                }
            )

    def write(self):
        super().write()
        self._write_441()


class ApplicationWriteIndexationService:
    """Сервис для записи информации о заявке в поисковый индекс."""
    _writer: ApplicationWriter

    def __init__(self, writer: ApplicationWriter, validator: ApplicationIndexationValidator = None):
        self._writer = writer
        self._validator = validator

    def write(self):
        if self._validator:
            try:
                self._validator.validate()
            except ValueError as e:
                logger.error(e)
            else:
                with transaction.atomic():
                    self._writer.write()
        else:
            with transaction.atomic():
                self._writer.write()


def create_service(app: IpcAppList, app_data: dict):
    if app.obj_type_id in (1, 2, 3):
        writer = ApplicationESInvUMLDWriter(app, app_data)
        validator = ApplicationIndexationInvUMLDValidator(app_data)
        return ApplicationWriteIndexationService(writer, validator)
    elif app.obj_type_id == 4:
        writer = ApplicationESTMWriter(app, app_data)
        validator = ApplicationIndexationTMValidator(app_data)
        return ApplicationWriteIndexationService(writer, validator)
    elif app.obj_type_id == 5:
        writer = ApplicationESGeoWriter(app, app_data)
        return ApplicationWriteIndexationService(writer)
    elif app.obj_type_id == 6:
        writer = ApplicationESIDWriter(app, app_data)
        validator = ApplicationIndexationIDValidator(app_data)
        return ApplicationWriteIndexationService(writer, validator)
    elif app.obj_type_id in (9, 14):
        writer = ApplicationESMadridWriter(app, app_data)
        return ApplicationWriteIndexationService(writer)
    elif app.obj_type_id in (10, 11, 12, 13, 17):
        writer = ApplicationESWriter(app, app_data)
        return ApplicationWriteIndexationService(writer)
    elif app.obj_type_id == 16:
        writer = ApplicationESInvCertWriter(app, app_data)
        return ApplicationWriteIndexationService(writer)
