import io
import datetime
import json
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING, Any

from django.conf import settings
from PIL import Image

from apps.search.models import ObjType, IpcAppList, ScheduleType
from apps.search.services.application_indexators import ApplicationIndexationService

if TYPE_CHECKING:
    from apps.wkm.models import WKMMark


class WKMConverter(ABC):
    """
    Інтерфейс конвертера для перетворення даних добре відомої ТМ у певну структуру даних.

    :cvar apps.search.models.WKMMark _record: екземпляр моделі добре відомої ТМ
    :cvar Any _res: результат конвертації.
    """
    _record: 'WKMMark'
    _res: dict

    def __init__(self, record: 'WKMMark') -> None:
        self._record = record
        self._res = {}

    @abstractmethod
    def convert(self) -> Any:
        raise NotImplemented


class WKMJSONConverter(WKMConverter):
    """
    Реалізація конвертера для отримання даних добре відомої ТМ у вигляді словника.

    :cvar apps.search.models.WKMMark _record: екземпляр моделі добре відомої ТМ
    :cvar dict _res: результат конвертації.
    """

    def convert(self) -> dict:
        """
        Головний метод класу, який формує кінцевий результат роботи конвертатора.

        :return результат конвертації
        :rtype dict
        """
        self.add_publication_details()
        self.add_decision_details()
        self.add_order_details()
        self.add_rights_date()
        self.add_word_mark_specification()
        self.add_court_comments()
        self.add_mark_image_details()
        self.add_vienna_classes()
        self.add_holders()
        self.add_nice_classes()
        return self._res

    def add_publication_details(self) -> None:
        self._res['PublicationDetails'] = [{
            'PublicationDate': self._record.bulletin.bulletin_date.strftime('%Y-%m-%d'),
            'PublicationIdentifier': self._record.bulletin.bull_str,
        }]

    def add_decision_details(self) -> None:
        if self._record.decision_date and self._record.decision_date.year != 1900:
            self._res.setdefault('DecisionDetails', {})['DecisionDate'] = \
                self._record.decision_date.strftime('%Y-%m-%d')
        if self._record.wkmdocument_set.filter(document_type__code='decision').exists():
            self._res.setdefault(
                'DecisionDetails', {}).setdefault('DecisionFile', {})['DecisionFilename'] = 'decision.pdf'

    def add_order_details(self) -> None:
        if self._record.order_date and self._record.order_date.year != 1900:
            self._res.setdefault('OrderDetails', {})['OrderDate'] = \
                self._record.order_date.strftime('%Y-%m-%d')
        if self._record.order_number:
            self._res.setdefault('OrderDetails', {})['OrderNumber'] = self._record.order_number
        order_doc_types = ['nakaz_dsiv', 'nakaz_minekonom1', 'nakaz_minekonom2']
        order_doc = self._record.wkmdocument_set.filter(document_type__code__in=order_doc_types).last()
        if order_doc:
            self._res.setdefault('OrderDetails', {})['OrderFile'] = {
                'OrderFilename': f"{order_doc.document_type.code}.pdf",
                'OrderType': order_doc.document_type.value
            }

    def add_rights_date(self) -> None:
        self._res['RightsDate'] = self._record.rights_date.strftime('%Y-%m-%d') if self._record.rights_date else None

    def add_word_mark_specification(self) -> None:
        self._res['WordMarkSpecification'] = {
            'MarkSignificantVerbalElement': [{
                '#text': self._record.keywords,
                '@sequenceNumber': 1
            }]
        }

    def add_court_comments(self) -> None:
        if self._record.court_comments_ua:
            self._res.setdefault('CourtComments', {})['CourtCommentsUA'] = self._record.court_comments_ua
        if self._record.court_comments_eng:
            self._res.setdefault('CourtComments', {})['CourtCommentsEN'] = self._record.court_comments_eng
        if self._record.court_comments_rus:
            self._res.setdefault('CourtComments', {})['CourtCommentsRU'] = self._record.court_comments_rus

    def add_mark_image_details(self) -> None:
        if self._record.mark_image:
            self._res.setdefault('MarkImageDetails', {}).setdefault('MarkImage', {}).update({
                'MarkImageFileFormat': 'JPG',
                'MarkImageFilename': f"{self._record.id}.jpg",
            })

    def add_vienna_classes(self) -> None:
        vienna_classes = [
            klass.class_number for klass in self._record.wkmvienna_set.order_by('class_number').all()
        ]
        if vienna_classes:
            self._res.setdefault('MarkImageDetails', {}).setdefault('MarkImage', {}).setdefault(
                'MarkImageCategory', {}
            ).setdefault('CategoryCodeDetails', {}).setdefault('CategoryCode', vienna_classes)

    def add_holders(self) -> None:
        for i, owner in enumerate(self._record.owners.order_by('pk').all(), 1):
            self._res.setdefault('HolderDetails', {}).setdefault('Holder', []).append({
                'HolderAddressBook': {
                    'FormattedNameAddress': {
                        'Address': {
                            'AddressCountryCode': owner.country_code
                        },
                        'Name': {
                            'FreeFormatName': {
                                'FreeFormatNameDetails': {
                                    'FreeFormatNameLine': owner.owner_name
                                }
                            }
                        }
                    }
                },
                'HolderSequenceNumber': i
            })

    def add_nice_classes(self) -> None:
        nice_classes = defaultdict(list)
        for klass in self._record.wkmclass_set.order_by('class_number', 'ord_num').all():
            nice_classes[klass.class_number].append({
                'ClassificationTermLanguageCode': 'UA',
                'ClassificationTermText': klass.products
            })
        for klass in nice_classes:
            self._res.setdefault('GoodsServicesDetails', {}).setdefault(
                'GoodsServices', {}).setdefault('ClassDescriptionDetails', {}).setdefault(
                'ClassDescription', []).append(
                {
                    'ClassNumber': klass,
                    'ClassificationTermDetails': {
                        'ClassificationTerm': nice_classes[klass]
                    }
                })


class WKMImportService:
    """
    Сервіс для імпорту Добре відомої ТМ у СІС.

    :cvar apps.search.models.WKMMark _wkm: екземпляр моделі добре відомої ТМ
    :cvar apps.search.models.ObjType _obj_type: тип ОПВ
    """

    _wkm: 'WKMMark'
    _obj_type: ObjType

    def __init__(self, wkm: 'WKMMark'):
        self._wkm = wkm
        self._obj_type = ObjType.objects.filter(code='WKM').first()

    @property
    def _files_path(self) -> str:
        """
        Повертає шлях до файлів добре відомого знака у файловому сховищі СІС.

        :return шлях до файлів добре відомого знака у файловому сховищі СІС
        :rtype str
        """
        return os.path.join(
            settings.MEDIA_ROOT,
            'WKM',
            str(self._wkm.rights_date.year),
            str(self._wkm.id),
            ''
        )

    def _create_files(self) -> None:
        """Створює файли добре відомого знаку (json з бібліографією та зображення) у файловому сховищі СІС."""
        os.makedirs(self._files_path, exist_ok=True)
        self._create_biblio_file()
        self._create_image()
        self._create_documents()

    def _create_biblio_file(self) -> None:
        """Створює файли json з бібліографією у файловому сховищі СІС."""
        files_path_for_json = self._files_path.replace(settings.MEDIA_ROOT, '//bear/share/').replace('/', '\\')
        wkm_converter = WKMJSONConverter(self._wkm)
        data = {
            'Document': {
                'idObjType': self._obj_type.pk,
                'filesPath': files_path_for_json
            },
            'WellKnownMark': {
                'WellKnownMarkDetails': wkm_converter.convert()
            }
        }
        with open(os.path.join(self._files_path, f"{self._wkm.id}.json"), 'w') as fp:
            json.dump(data, fp, ensure_ascii=False)

    def _create_image(self) -> None:
        """Створює зображення у файловому сховищі СІС."""
        image_data = self._wkm.mark_image
        if image_data:
            image = Image.open(io.BytesIO(image_data))
            image.save(os.path.join(self._files_path, f"{self._wkm.id}.jpg"), format='JPEG')

    def _create_documents(self) -> None:
        """Створює файли у файловому сховищі СІС."""
        for doc in self._wkm.wkmdocument_set.all():
            file_name = f"{doc.document_type.code}.pdf"
            with open(os.path.join(self._files_path, file_name), 'wb') as f:
                f.write(doc.file)

    def _create_or_update_db_record(self) -> IpcAppList:
        """Створює або оновлює запис у БД UMA."""
        app = IpcAppList.objects.filter(obj_type=self._obj_type, id_parent=self._wkm.id).first()
        if not app:
            app = IpcAppList()
        app.registration_date = self._wkm.rights_date
        app.id_shedule_type = ScheduleType.objects.filter(obj_type=self._obj_type).first().pk
        app.files_path = self._files_path.replace(settings.MEDIA_ROOT, '//bear/share/').replace('/', '\\')
        app.id_parent = self._wkm.id
        app.id_claim = self._wkm.id
        app.obj_type = self._obj_type
        app.changescount += 1
        app.lastupdate = datetime.datetime.now()
        app.elasticindexed = 0
        app.save()

        return app

    def execute(self) -> IpcAppList:
        """Головний метод класу, який виконує роботу по імпорту добре відомої ТМ у СІС."""
        # Створити файли з даними і зображенням у файловому сховищі
        self._create_files()

        # Створити/оновити запис у БД UMA
        app = self._create_or_update_db_record()

        # Пошукова індексація
        indexation_service = ApplicationIndexationService()
        indexation_service.index_application(app)

        return app
