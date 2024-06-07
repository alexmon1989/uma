from django.db.models import F, QuerySet, Prefetch, Q as Q_ORM
from django.conf import settings

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from rest_framework import exceptions

from apps.search.models import IpcAppList, AppDocuments
import apps.search.services as search_services
from apps.api.models import OpenData
from apps.bulletin import services as bulletin_services

from typing import List, Optional, Union, Set
from datetime import datetime
from abc import ABC, abstractmethod
import json


def app_get_api_list(options: dict) -> List:
    """Возвращает список объектов для добавления в API"""
    apps = IpcAppList.objects.filter(
        elasticindexed=1
    ).exclude(
        obj_type_id__in=(9, 14)
    ).annotate(
        app_id=F('id'), last_update=F('lastupdate')
    ).values_list('app_id', 'last_update')

    # Объекты в API
    api_apps = OpenData.objects.values_list('app_id', 'last_update')

    # Фильтр по параметру id (если в API нужно добавить только определённую заявку)
    if options['id']:
        apps = apps.filter(id=options['id'])
        api_apps = api_apps.filter(app_id=options['id'])

    # Фильтр по типу объекта
    if options['obj_type_ids']:
        apps = apps.filter(obj_type_id__in=options['obj_type_ids'])
        api_apps = api_apps.filter(obj_type_id__in=options['obj_type_ids'])

    # Объекты, которых нет в API (или которые имеют другое значение поля last_update)
    if options['not_compare_last_update']:
        diff = apps
    else:
        diff = list(set(apps) - set(api_apps))

    return diff


def app_get_claim_from_es(app_number: str) -> dict:
    """Возвращает данные заявки (search_data.obj_state:1) из ES."""
    es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    claim = Search(
        using=es,
        index=settings.ELASTIC_INDEX_NAME
    ).query(
        Q(
            'query_string',
            query=f"search_data.obj_state:1 AND search_data.app_number:{app_number}"
        )
    ).source(
        excludes=["*.DocBarCode", "*.DOCBARCODE"]
    ).execute()
    if claim:
        return claim[0].to_dict()
    return {}


def app_get_payments(app_data: dict) -> Optional[Union[dict, List]]:
    """Возвращает платежи по заявке"""
    # Платежи по изобретениям, полезным моделям, топографиям
    if app_data['Document']['idObjType'] in (1, 2, 3):
        res = {
            'payments': app_data.get('DOCFLOW', {}).get('PAYMENTS', []),
            'collections': app_data.get('DOCFLOW', {}).get('COLLECTIONS', []),
        }

        # Если это охранный документ, то необходимо объеденить с платежами по заявке
        if app_data['search_data']['obj_state'] == 2:
            claim = app_get_claim_from_es(app_data['search_data']['app_number'])
            if claim:
                if claim.get('DOCFLOW', {}).get('PAYMENTS'):
                    res['payments'].extend(claim['DOCFLOW']['PAYMENTS'])
                if claim.get('DOCFLOW', {}).get('COLLECTIONS'):
                    res['collections'].extend(claim['DOCFLOW']['COLLECTIONS'])

        return res

    # Платежи по ТМ
    elif app_data['Document']['idObjType'] == 4:
        return app_data.get('TradeMark', {}).get('PaymentDetails')

    # Платежи по пром. образцам
    elif app_data['Document']['idObjType'] == 6:
        return app_data.get('Design', {}).get('PaymentDetails')

    # По другим объектам платежей пока нет
    else:
        return None


def app_get_documents(app_data: dict) -> Optional[Union[dict, List]]:
    """Возвращает документы по заявке."""
    # Документы по изобретениям, полезным можелям, топографиям
    if app_data['Document']['idObjType'] in (1, 2, 3):
        res = app_data.get('DOCFLOW', {}).get('DOCUMENTS', [])

        # Если это охранный документ, то необходимо объеденить с документами по заявке
        if app_data['search_data']['obj_state'] == 2:
            claim = app_get_claim_from_es(app_data['search_data']['app_number'])
            if claim and claim.get('DOCFLOW', {}).get('DOCUMENTS'):
                res.extend(claim['DOCFLOW']['DOCUMENTS'])

        # Не включать документы без номера и даты
        res = list(filter(lambda x: x['DOCRECORD'].get('DOCREGNUMBER') or x['DOCRECORD'].get('DOCSENDINGDATE'), res))

        if res:
            return res
        else:
            return None

    # Документы по ТМ
    elif app_data['Document']['idObjType'] == 4:
        return app_data['TradeMark'].get('DocFlow', {}).get('Documents')

    # КЗПТ
    elif app_data['Document']['idObjType'] == 5:
        return app_data['Geo'].get('DocFlow', {}).get('Documents')

    # Документы по пром. образцам
    elif app_data['Document']['idObjType'] == 6:
        return app_data['Design'].get('DocFlow', {}).get('Documents')

    # Документы по пром. образцам
    elif app_data['Document']['idObjType'] in (10, 13):
        return app_data['Certificate']['CopyrightDetails'].get('DocFlow', {}).get('Documents')

    # Документы по пром. образцам
    elif app_data['Document']['idObjType'] in (11, 12):
        return app_data['Decision']['DecisionDetails'].get('DocFlow', {}).get('Documents')

    # По другим объектам документов пока нет
    else:
        return None


def app_get_tm_biblio_for_opendata(app_data: dict) -> dict:
    """Возвращает словарь с минимумом данных заявки на ТМ для публикации в API"""
    return {
        'ApplicationNumber': app_data['search_data']['app_number'],
        'ApplicationDate': app_data['search_data']['app_date'],
        'MarkImageDetails': app_data['TradeMark']['TrademarkDetails'].get('MarkImageDetails'),
        'WordMarkSpecification': app_data['TradeMark']['TrademarkDetails'].get('WordMarkSpecification'),
        'GoodsServicesDetails': app_data['TradeMark']['TrademarkDetails'].get('GoodsServicesDetails'),
        'stages': app_data['TradeMark']['TrademarkDetails'].get('stages'),
    }


def app_get_tm_app_status(app_data: dict) -> str:
    """Возвращает статус заявки на ТМ."""
    mark_status_code = int(app_data['Document'].get('MarkCurrentStatusCodeType', 0))
    is_stopped = app_data['Document'].get('RegistrationStatus') == 'Діловодство за заявкою припинено' \
                 or mark_status_code == 8000 \
                 or app_data.get('TradeMark', {}).get('TrademarkDetails', {}).get('application_status') == 'stopped'
    return 'stopped' if is_stopped else 'active'


def app_get_biblio_data(app_data: dict) -> Optional[dict]:
    """Возвращает библиографические данные заявки."""
    # Библ. данные заявок без установленной даты подачи на изобретения не публикуются
    if app_data['Document']['idObjType'] == 1 \
            and app_data['search_data']['obj_state'] == 1 \
            and not app_data['Claim'].get('I_43.D'):
        data_biblio = None

    # Библ. данные заявок на полезные модели и топографии не публикуются
    elif app_data['Document']['idObjType'] in (2, 3) and app_data['search_data']['obj_state'] == 1:
        data_biblio = None

    # Библ. данные по изобретениям, полезным можелям, топографиям
    elif app_data['Document']['idObjType'] in (1, 2, 3):
        data_biblio = app_data.get('Patent', app_data.get('Claim'))

    # Свидетельства на знаки для товаров и услуг
    elif app_data['Document']['idObjType'] == 4:
        # Если есть свидетельство или 441 код - публикуется вся библиография
        if app_data['search_data']['obj_state'] == 2 or 'Code_441' in app_data['TradeMark']['TrademarkDetails']:
            data_biblio = app_data['TradeMark']['TrademarkDetails']
        else:
            app_date = app_data['TradeMark']['TrademarkDetails'].get('ApplicationDate')
            mark_status = search_services.application_get_tm_fixed_mark_status_code(app_data)
            # Если заявка до 18.07.2020 - проверяется MarkCurrentStatusCodeType
            if (app_date
                and datetime.strptime(app_date[:10], '%Y-%m-%d') < datetime.strptime('2020-07-18', '%Y-%m-%d')
                and mark_status >= 2000) or mark_status >= 3000:
                # Публикуется вся библиография
                data_biblio = app_data['TradeMark']['TrademarkDetails']
            else:
                # Публикуется часть библиографии для API
                data_biblio = app_get_tm_biblio_for_opendata(app_data)

        # Статус заявки
        if data_biblio and app_data['search_data']['obj_state'] == 1:
            data_biblio['application_status'] = app_get_tm_app_status(app_data)

    # КЗПТ
    elif app_data['Document']['idObjType'] == 5:
        if app_data['search_data']['obj_state'] == 1 \
                and 'ApplicationPublicationDetails' not in app_data['Geo']['GeoDetails']:
            data_biblio = None
        else:
            data_biblio = app_data['Geo']['GeoDetails']

    # Патенты на пром. образцы
    elif app_data['Document']['idObjType'] == 6:
        # Записывается только библиография патентов
        data_biblio = app_data['Design']['DesignDetails'] if app_data['search_data']['obj_state'] == 2 else None

    # Авторське право
    elif app_data['Document']['idObjType'] in (10, 13):
        if app_data['Certificate']['CopyrightDetails'].get('DocFlow'):
            del app_data['Certificate']['CopyrightDetails']['DocFlow']
        data_biblio = app_data['Certificate']['CopyrightDetails']

    # Авторське право (договора)
    elif app_data['Document']['idObjType'] in (11, 12):
        if app_data['Decision']['DecisionDetails'].get('DocFlow'):
            del app_data['Decision']['DecisionDetails']['DocFlow']
        data_biblio = app_data['Decision']['DecisionDetails']

    # СДО
    elif app_data['Document']['idObjType'] == 16:
        data_biblio = app_data['Patent_Certificate']

    else:
        data_biblio = None

    if app_data['search_data']['obj_state'] == 2 and data_biblio:
        data_biblio['registration_status_color'] = app_data['search_data']['registration_status_color']

    # Стадии заявки
    stages = search_services.application_get_stages_statuses(app_data)
    if stages:
        if data_biblio:
            data_biblio['stages'] = stages
        else:
            data_biblio = {'stages': stages}

    return data_biblio


def app_get_unique_subjects_from_data(data: dict) -> Set[str]:
    """Возвращает множество с наименованиями субъектов, которые имеют отношение к заявке."""
    res = set()
    for person_type in ('applicant', 'inventor', 'owner', 'agent'):
        try:
            if data['search_data'].get(person_type):
                for person in data['search_data'][person_type]:
                    res.add(person['name'])
        except KeyError:
            pass
    return res


def app_get_short_biblio(data: dict) -> dict:
    app_get_short_biblio_tm(data)
    return {}


def app_get_short_biblio_tm(data: dict) -> dict:
    return {}


def app_get_short_biblio_id(data: dict) -> dict:
    return {}


def opendata_prepare_filters(query_params: dict) -> dict:
    """Возвращает провалидированные значения фильтров."""
    res = {}

    # Целочисленные фильтры
    filters = (
        'obj_state',  # Стан об'єкта
        'obj_type',  # Тип об'єкта
    )
    for key in filters:
        value = query_params.get(key)
        if value:
            try:
                value = int(value)
            except ValueError:
                raise exceptions.ParseError(f"Невірне значення параметру {key}")
            else:
                res[key] = value

    # Фильтры даты
    filters = (
        'app_date_from',  # Дата заявки від
        'app_date_to',  # Дата заявки від
        'reg_date_from',  # Дата реєстрації від
        'reg_date_to',  # Дата реєстрації до
        'last_update_from',  # Дата останньої зміни від
        'last_update_to',  # Дата останньої зміни до
    )
    for key in filters:
        value = query_params.get(key)
        if value:
            try:
                value = datetime.strptime(value, '%d.%m.%Y')
            except (ValueError, TypeError):
                raise exceptions.ParseError(f"Невірне значення параметру {key}")
            else:
                res[key] = value

    # Номер заявки
    if query_params.get('app_number'):
        res['app_number'] = query_params['app_number']

    # Имя субъекта
    if query_params.get('subject_name'):
        if len(query_params['subject_name']) > 255:
            raise exceptions.ParseError(f"Параметр subject_name має бути не більшим за 255 символів")
        res['subject_name'] = query_params['subject_name']

    return res


def opendata_get_ids_queryset(filters: dict) -> QuerySet[OpenData]:
    """Возвращает Queryset (с применением фильтров) с id заявок для API."""
    queryset = OpenData.objects.filter(is_visible=True).order_by('pk').all()

    # Стан об'єкта
    if filters.get('obj_state'):
        queryset = queryset.filter(obj_state=filters['obj_state'])

    # Тип об'єкта
    if filters.get('obj_type'):
        queryset = queryset.filter(obj_type_id=filters['obj_type'])

    # Дата заявки від
    if filters.get('app_date_from'):
        queryset = queryset.filter(app_date__gte=filters['app_date_from'].replace(hour=0, minute=0, second=0))

    # Дата заявки до
    if filters.get('app_date_to'):
        queryset = queryset.filter(app_date__lte=filters['app_date_to'].replace(hour=23, minute=59, second=59))

    # Дата реєстрації від
    if filters.get('reg_date_from'):
        queryset = queryset.filter(registration_date__gte=filters['reg_date_from'].replace(hour=0, minute=0, second=0))

    # Дата реєстрації до
    if filters.get('reg_date_to'):
        queryset = queryset.filter(registration_date__lte=filters['reg_date_to'].replace(hour=23, minute=59, second=59))

    # Дата останньої зміни від
    if filters.get('last_update_from'):
        queryset = queryset.filter(last_update__gte=filters['last_update_from'].replace(hour=0, minute=0, second=0))

    # Дата останньої зміни до
    if filters.get('last_update_to'):
        queryset = queryset.filter(last_update__lte=filters['last_update_to'].replace(hour=23, minute=59, second=59))

    # Номер заявки
    if filters.get('app_number'):
        queryset = queryset.filter(app_number=filters['app_number'])

    # Имя субъекта
    if filters.get('subject_name'):
        queryset = queryset.filter(person__person_name__contains_ft=' AND '.join(filters['subject_name'].split()))

    return queryset.distinct().values_list('id', flat=True)


def opendata_get_applications(ids: List[int]) -> List[dict]:
    """Возвращает список данных заявок по их идентификаторам."""
    apps = OpenData.objects.select_related('obj_type').prefetch_related(
        Prefetch(
            'app__appdocuments_set',
            queryset=AppDocuments.objects.filter(file_type='pdf', app__is_limited=False),
        )
    ).filter(pk__in=ids)
    res = []
    for app in apps:
        item = {
            'id': app.pk,
            'obj_type_id': app.obj_type.pk,
            'obj_state': app.obj_state,
            'app_number': app.app_number,
            'app_date': app.app_date,
            'registration_number': app.registration_number,
            'registration_date': app.registration_date,
            'last_update': app.last_update,
            'data': app.data,
            'data_docs': app.data_docs,
            'data_payments': app.data_payments,
            'obj_type__obj_type_ua': app.obj_type.obj_type_ua,
            'files_path': app.files_path,
        }
        files = []
        for f in app.app.appdocuments_set.all():
            files.append(f.file_name.replace(
                '\\\\bear\share\\', settings.MEDIA_URL
            ).replace('\\', '/'))
        item['files'] = files
        res.append(item)
    return res


def opendata_get_application(app_number: str, obj_type_id: int = None) -> dict | None:
    """Возвращает данные заявки"""
    queryset = OpenData.objects.filter(
        is_visible=True
    ).select_related('obj_type').prefetch_related(
        Prefetch(
            'app__appdocuments_set',
            queryset=AppDocuments.objects.filter(file_type='pdf', app__is_limited=False),
        )
    ).order_by('-registration_number').filter(
        Q_ORM(app_number=app_number) | Q_ORM(registration_number=app_number)
    )

    if obj_type_id:
        queryset = queryset.filter(obj_type_id=obj_type_id)

    app = queryset.first()
    if app:
        item = {
            'id': app.pk,
            'obj_type_id': app.obj_type.pk,
            'obj_state': app.obj_state,
            'app_number': app.app_number,
            'app_date': app.app_date,
            'registration_number': app.registration_number,
            'registration_date': app.registration_date,
            'last_update': app.last_update,
            'data': app.data,
            'data_docs': app.data_docs,
            'data_payments': app.data_payments,
            'obj_type__obj_type_ua': app.obj_type.obj_type_ua,
            'files_path': app.files_path,
        }
        files = []
        for f in app.app.appdocuments_set.all():
            files.append(f.file_name.replace(
                '\\\\bear\share\\', settings.MEDIA_URL
            ).replace('\\', '/'))
        item['files'] = files

        return item

    return None


class BiblioDataPresenter(ABC):
    """Готовит библиографические данные к отображению в API."""
    _application_data: dict

    @property
    def _files_dir(self) -> str:
        """Возвращает путь к каталогу с файлами заявки."""
        return self._application_data['files_path'].replace(
            '\\\\bear\share\\', settings.MEDIA_URL
        ).replace('\\', '/')

    def set_application_data(self, application_data: dict):
        self._application_data = application_data

    @abstractmethod
    def get_prepared_biblio(self) -> dict:
        pass


class BiblioDataFullPresenter(BiblioDataPresenter):
    """Готовит полные библиографические данные к отображению в API."""
    files_dir = None
    _raw_biblio: dict
    _prepare_methods: dict

    def __init__(self):
        self._prepare_methods = {
            4: self._prepare_biblio_tm,
            6: self._prepare_biblio_id,
            10: self._prepare_biblio_copyright,
            11: self._prepare_biblio_copyright,
            12: self._prepare_biblio_copyright,
            13: self._prepare_biblio_copyright,
        }

    def _prepare_biblio_tm(self) -> None:
        """Готовит полные библиографические данные для ТМ."""
        bulletin_date_until = datetime.strptime(
            settings.CODE_441_BUL_NUMBER_FROM_JSON_SINCE_DATE,
            '%d.%m.%Y'
        )

        if 'Code_441_BulNumber' in self._raw_biblio:
            # Fix случая когда приходил неверный номер бюлетня
            if 'Code_441' in self._raw_biblio and self._application_data['last_update'] < bulletin_date_until:
                self._raw_biblio['Code_441_BulNumber'] = bulletin_services.bulletin_get_number_by_date(
                    self._raw_biblio['Code_441']
                )
            # Fix типа данных поля 'Code_441_BulNumber'
            self._raw_biblio['Code_441_BulNumber'] = str(self._raw_biblio['Code_441_BulNumber'])

        # Fix типа данных поля 'ApplicantSequenceNumber'
        if 'ApplicantDetails' in self._raw_biblio:
            for applicant in self._raw_biblio['ApplicantDetails']['Applicant']:
                applicant['ApplicantSequenceNumber'] = int(applicant['ApplicantSequenceNumber'])

        # Fix типа данных поля 'HolderSequenceNumber'
        if 'HolderDetails' in self._raw_biblio:
            for applicant in self._raw_biblio['HolderDetails']['Holder']:
                applicant['HolderSequenceNumber'] = int(applicant['HolderSequenceNumber'])

        # Fix типа данных поля '@sequenceNumber' секции 'WordMarkSpecification'
        if self._raw_biblio.get('WordMarkSpecification'):
            for item in self._raw_biblio['WordMarkSpecification']['MarkSignificantVerbalElement']:
                if '@sequenceNumber' in item:
                    try:
                        item['@sequenceNumber'] = int(item['@sequenceNumber'])
                    except ValueError:
                        item['@sequenceNumber'] = 1

        # Fix типа данных поля 'ClassNumber' секции 'GoodsServicesDetails'
        if self._raw_biblio.get('GoodsServicesDetails') \
                and 'ClassDescription' in self._raw_biblio['GoodsServicesDetails']['GoodsServices'][
            'ClassDescriptionDetails']:
            for item in self._raw_biblio['GoodsServicesDetails']['GoodsServices']['ClassDescriptionDetails'][
                'ClassDescription']:
                item['ClassNumber'] = int(item['ClassNumber'])

        # Fix типа данных поля '@sequenceNumber' секции 'MarkImageDetails'
        if 'MarkImageDetails' in self._raw_biblio:
            if 'MarkImageColourClaimedText' in self._raw_biblio['MarkImageDetails']['MarkImage']:
                for item in self._raw_biblio['MarkImageDetails']['MarkImage']['MarkImageColourClaimedText']:
                    if '@sequenceNumber' in item:
                        try:
                            item['@sequenceNumber'] = int(item['@sequenceNumber'])
                        except ValueError:
                            item['@sequenceNumber'] = 1

            # Fix типов данных полей секции 'MarkImageRepresentationSize'
            if self._raw_biblio['MarkImageDetails'].get('MarkImage', {}).get('MarkImageRepresentationSize'):
                for item in self._raw_biblio['MarkImageDetails']['MarkImage']['MarkImageRepresentationSize']:
                    if 'Height' in item['MarkImageRenditionRepresentationSize']:
                        try:
                            item['MarkImageRenditionRepresentationSize']['Height'] = int(
                                item['MarkImageRenditionRepresentationSize']['Height']
                            )
                        except ValueError:
                            item['MarkImageRenditionRepresentationSize']['Height'] = 0

                    if 'Width' in item['MarkImageRenditionRepresentationSize']:
                        try:
                            item['MarkImageRenditionRepresentationSize']['Width'] = int(
                                item['MarkImageRenditionRepresentationSize']['Width']
                            )
                        except ValueError:
                            item['MarkImageRenditionRepresentationSize']['Width'] = 0

        # Fix типа данных поля 'PriorityPartialIndicator' секции 'PriorityDetails'
        if 'PriorityDetails' in self._raw_biblio and 'Priority' in self._raw_biblio['PriorityDetails']:
            for item in self._raw_biblio['PriorityDetails']['Priority']:
                if type(item['PriorityPartialIndicator']) is str:
                    if item['PriorityPartialIndicator'] == 'true':
                        item['PriorityPartialIndicator'] = True
                    else:
                        item['PriorityPartialIndicator'] = False

        # Fix типа данных поля 'ExhibitionPartialIndicator' секции 'ExhibitionPriorityDetails'
        if 'ExhibitionPriorityDetails' in self._raw_biblio:
            for item in self._raw_biblio['ExhibitionPriorityDetails']['ExhibitionPriority']:
                if type(item['ExhibitionPartialIndicator']) is str:
                    if item['ExhibitionPartialIndicator'] == 'true':
                        item['ExhibitionPartialIndicator'] = True
                    else:
                        item['ExhibitionPartialIndicator'] = False

        # Полные пути к изображениям
        try:
            image_name = self._raw_biblio['MarkImageDetails']['MarkImage']['MarkImageFilename']
            self._raw_biblio['MarkImageDetails']['MarkImage']['MarkImageFilename'] = f"{self._files_dir}{image_name}"
        except (KeyError, TypeError):
            pass

    def _prepare_biblio_id(self) -> None:
        """Готовит полные библиографические данные для пром. образца."""
        # Фильтрация библиографических данных
        if 'DesignerDetails' in self._raw_biblio and 'Designer' in self._raw_biblio['DesignerDetails']:
            for i, designer in enumerate(self._raw_biblio['DesignerDetails']['Designer']):
                # Значение поля Publicated - признак того надо ли публиковать автора
                if 'Publicated' in designer and not designer['Publicated']:
                    del self._raw_biblio['DesignerDetails']['Designer'][i]

        # Полные пути к изображениям
        try:
            images = self._raw_biblio['DesignSpecimenDetails'][0]['DesignSpecimen']
            for image in images:
                image['SpecimenFilename'] = f"{self._files_dir}{image['SpecimenFilename']}"
        except (KeyError, TypeError):
            pass

    def _prepare_biblio_copyright(self):
        """Готовит полные библиографические данные для авторского права."""

        # Удаление наименования автора если аноним или псевдоним
        try:
            for author in self._raw_biblio['AuthorDetails']['Author']:
                if author['AuthorAddressBook']['FormattedNameAddress']['Name']['FreeFormatName']['RepresentNameFormDetails']['RepresentNameForm']:
                    del author['AuthorAddressBook']['FormattedNameAddress']['Name']['FreeFormatName']['FreeFormatNameDetails']
        except KeyError:
            pass

        # Удаление DocBarCode
        try:
            doc_flow = self._raw_biblio['DocFlow']['Documents']
            for doc in doc_flow:
                del doc['DocRecord']['DocBarCode']
        except (KeyError, TypeError):
            pass

    def get_prepared_biblio(self) -> dict:
        self._raw_biblio = json.loads(self._application_data['data'])

        # Подготовка данных в зависимости от типа объекта
        if self._application_data['obj_type_id'] in self._prepare_methods:
            self._prepare_methods[self._application_data['obj_type_id']]()

        return self._raw_biblio


class BiblioDataNacpPresenter(BiblioDataPresenter):
    """Готовит библиографические данные к отображению в API (для НАЗК)."""

    def __init__(self):
        self._prepare_methods = {
            1: self._prepare_biblio_id_um_ld,
            2: self._prepare_biblio_id_um_ld,
            3: self._prepare_biblio_id_um_ld,
            4: self._prepare_biblio_tm,
            5: self._prepare_biblio_geo,
            6: self._prepare_biblio_id,
            10: self._prepare_biblio_copyright,
            11: self._prepare_biblio_agreement,
            12: self._prepare_biblio_agreement,
            13: self._prepare_biblio_copyright,
        }

    def _prepare_biblio_geo(self, raw_biblio: dict) -> dict:
        """Возвращает библиографические данные длягеогр. зазначень"""
        return {
            'Indication': raw_biblio.get('Indication'),
            'HolderDetails': raw_biblio.get('HolderDetails'),
            'RepresentativeDetails': raw_biblio.get('RepresentativeDetails'),
        }

    def _prepare_biblio_copyright(self, raw_biblio: dict) -> dict:
        """Возвращает библиографические данные для авт. права."""
        return {
            'Name': raw_biblio.get('Name'),
            'AuthorDetails': raw_biblio.get('AuthorDetails'),
        }

    def _prepare_biblio_agreement(self, raw_biblio: dict) -> dict:
        """Возвращает библиографические данные для договоров авт. права."""
        return {
            'Name': raw_biblio.get('Name'),
            'AuthorDetails': raw_biblio.get('AuthorDetails'),
            'LicensorDetails': raw_biblio.get('LicensorDetails'),
            'LicenseeDetails': raw_biblio.get('LicenseeDetails'),
        }

    def _prepare_biblio_id_um_ld(self, raw_biblio: dict) -> dict:
        """Возвращает библиографические данные для изобретений, полезных моделей, топографий."""
        return {
            'I_54': raw_biblio.get('I_54'),
            'I_71': raw_biblio.get('I_71'),
            'I_72': raw_biblio.get('I_72'),
            'I_73': raw_biblio.get('I_73'),
            'I_74': raw_biblio.get('I_74'),
            'I_98': raw_biblio.get('I_98'),
        }

    def _prepare_biblio_tm(self, raw_biblio: dict) -> dict:
        """Возвращает библиографические данные для ТМ."""
        data = {
            'ApplicantDetails': raw_biblio.get('ApplicantDetails'),
            'HolderDetails': raw_biblio.get('HolderDetails'),
            'RepresentativeDetails': raw_biblio.get('RepresentativeDetails'),
            'CorrespondenceAddress': raw_biblio.get('CorrespondenceAddress'),
            'MarkImageDetails': raw_biblio.get('MarkImageDetails'),
            'WordMarkSpecification': raw_biblio.get('WordMarkSpecification'),
        }

        # Полные пути к изображениям
        try:
            image_name = data['MarkImageDetails']['MarkImage']['MarkImageFilename']
            data['MarkImageDetails']['MarkImage']['MarkImageFilename'] = f"{self._files_dir}{image_name}"
        except (KeyError, TypeError):
            pass

        return data

    def _prepare_biblio_id(self, raw_biblio: dict) -> dict:
        """Возвращает библиографические данные для пром. образца."""
        data = {
            'ApplicantDetails': raw_biblio.get('ApplicantDetails'),
            'HolderDetails': raw_biblio.get('HolderDetails'),
            'DesignerDetails': raw_biblio.get('DesignerDetails'),
            'RepresentativeDetails': raw_biblio.get('RepresentativeDetails'),
            'CorrespondenceAddress': raw_biblio.get('CorrespondenceAddress'),
            'DesignTitle': raw_biblio.get('DesignTitle'),
        }

        if 'DesignerDetails' in data and 'Designer' in data['DesignerDetails']:
            for i, designer in enumerate(data['DesignerDetails']['Designer']):
                # Значение поля Publicated - признак того надо ли публиковать автора
                if 'Publicated' in designer and not designer['Publicated']:
                    del data['DesignerDetails']['Designer'][i]

        return data

    def get_prepared_biblio(self) -> dict:
        raw_biblio = json.loads(self._application_data['data'])
        return self._prepare_methods[self._application_data['obj_type_id']](raw_biblio)


class PaymentsDataPresenter(ABC):
    """Готовит данные платежей к отображению в API."""
    _payments_data: dict

    def set_payments_data(self, payments_data: dict):
        self._payments_data = payments_data

    @abstractmethod
    def get_prepared_payments(self) -> dict:
        pass


class PaymentsDataPresenterTmId(PaymentsDataPresenter):
    def get_prepared_payments(self) -> dict:
        if 'Payment' in self._payments_data:
            for payment in self._payments_data['Payment']:
                payment['PaymentFeeDetails']['FeeAmount']['Amount'] = str(
                    payment['PaymentFeeDetails']['FeeAmount']['Amount']
                )
        return self._payments_data


class DocumentsDataPresenter(ABC):
    """Готовит данные платежей к отображению в API."""
    _documents_data: dict

    def set_documents_data(self, documents_data: dict):
        self._documents_data = documents_data

    @abstractmethod
    def get_prepared_documents(self) -> dict:
        pass


class DocumentsDataPresenterTmId(DocumentsDataPresenter):
    def get_prepared_documents(self) -> dict:
        for doc in self._documents_data:
            if not doc['DocRecord'].get('DocIdDocCEAD'):
                doc['DocRecord']['DocIdDocCEAD'] = None
        return self._documents_data
