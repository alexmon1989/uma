from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.db.models import Max, Q as Q_db
from django.utils import timezone
from elasticsearch import Elasticsearch, exceptions as elasticsearch_exceptions
from elasticsearch_dsl import Search, Q
from apps.search.models import IpcAppList, IndexationError, IndexationProcess
from apps.search.services import services as search_services
from apps.bulletin.models import EBulletinData
from apps.bulletin.services import bulletin_get_number_with_year_by_date
from ...utils import get_registration_status_color, filter_bad_apps, delete_files_in_directory
import json
import os
import datetime
import shutil
import re
import pyodbc


class Command(BaseCommand):
    help = 'Adds or updates documents in ElasticSearch index.'
    es = None
    indexation_process = None
    is_limited_publication = False  # Признак что публикация с ограниченными данными

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            help='Index only one record with certain idAPPNumber from table IPC_AppLIST'
        )
        parser.add_argument(
            '--obj_type',
            type=int,
            help='Add to index only records with certain object type. '
                 'Values: '
                 '1 - Inventions, '
                 '2 - Utility models, '
                 '3 - Layout Designs (Topographies) of Integrated Circuit, '
                 '4 - Trade Marks, '
                 '5 - Qualified indications of the origin of goods, '
                 '6 - Industrial designs'
        )
        parser.add_argument(
            '--status',
            type=int,
            help='Add to index only records with certain status: 1 - applications, 2 - protective documents.'
        )
        parser.add_argument(
            '--ignore_indexed',
            type=bool,
            help='Ignores elasticindexed=1'
        )

    def get_doc_files_path(self, doc):
        # Путь к файлам объекта
        doc_files_path = doc['files_path'].replace(
            '\\\\bear\\share\\',
            settings.DOCUMENTS_MOUNT_FOLDER
        ).replace(
            'e:\\poznach_test_sis\\bear_tmpp_sis\\',
            settings.DOCUMENTS_MOUNT_FOLDER
        ).replace('\\', '/')

        return doc_files_path

    def get_json_path(self, doc):
        """Получает путь к файлу JSON с данными объекта."""
        # Путь к файлам объекта
        doc_files_path = self.get_doc_files_path(doc)

        # Если путь к файлу указан сразу (случай с авторским правом)
        if '.json' in doc_files_path:
            return doc_files_path

        # Путь к файлу JSON с данными объекта:
        file_name = doc['registration_number'] \
            if (doc['registration_number'] and doc['registration_number'] != '0') \
            else doc['app_number']
        file_name = file_name.replace('/', '_')

        json_path = os.path.join(doc_files_path, f"{file_name}.json")

        # Случай если охранные документы имеют название заявки
        if not os.path.exists(json_path) and doc['obj_type_id'] in (4, 5, 6,):
            file_name = doc['app_number'].replace('/', '_')
            json_path = os.path.join(doc_files_path, f"{file_name}.json")

        return json_path

    def get_data_from_json(self, doc):
        """Получает словарь с данными из файла JSON."""
        json_path = self.get_json_path(doc)

        data = None

        # Чтение содержимого JSON в data
        try:
            f = open(json_path, 'r', encoding='utf16')
            try:
                file_content = str.encode(f.read())
                file_content = file_content.replace(b'\xef\xbb\xbf', b'')
                data = json.loads(file_content)
            except json.decoder.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"JSONDecodeError: {e}: {json_path}"))
                IndexationError.objects.create(
                    app_id=doc['id'],
                    type='JSONDecodeError',
                    text=e,
                    json_path=json_path,
                    indexation_process=self.indexation_process
                )
        except (UnicodeDecodeError, UnicodeError):            
            try:
                f = open(json_path, 'r', encoding='utf-8')
                data = json.loads(f.read())
            except json.decoder.JSONDecodeError as e:
                try:
                    f = open(json_path, 'r', encoding='utf-8-sig')
                    data = json.loads(f.read())
                except json.decoder.JSONDecodeError as e:
                    self.stdout.write(self.style.ERROR(f"JSONDecodeError: {e}: {json_path}"))
                    IndexationError.objects.create(
                        app_id=doc['id'],
                        type='JSONDecodeError',
                        text=e,
                        json_path=json_path,
                        indexation_process=self.indexation_process
                    )
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"FileNotFoundError: {e}"))
            IndexationError.objects.create(
                app_id=doc['id'],
                type='FileNotFoundError',
                text=e,
                json_path=json_path,
                indexation_process=self.indexation_process
            )

        return data

    def fix_id_doc_cead(self, documents):
        """Получает idDocCead из БД EArchive, если он отсутсвует в JSON."""
        for doc in documents:
            if not doc['DocRecord'].get('DocIdDocCEAD') and doc['DocRecord'].get('DocBarCode'):
                with connections['e_archive'].cursor() as cursor:
                    cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
                    cursor.execute(
                        "SELECT idDoc FROM EArchive WHERE BarCODE=%s",
                        [doc['DocRecord'].get('DocBarCode', '')]
                    )
                    row = cursor.fetchone()
                    if row:
                        doc['DocRecord']['DocIdDocCEAD'] = row[0]

    def process_inv_um_ld(self, doc):
        """Добавляет документ одного из типов (изобретение, полезная модель, топография ИМС) в ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)

        res = {}
        # Проверка не выдан ли патент по заявке
        # if data is not None and not (data.get('Document').get('Status') == 3 and data.get('Claim', {}).get('I_11')):
        if data is not None:
            # Секция Document
            res['Document'] = data.get('Document')

            # Бибилиография
            biblio_data = None
            if data.get('Patent'):
                biblio_data = data['Patent']
                res['Patent'] = biblio_data
            elif data.get('Claim'):
                biblio_data = data['Claim']
                res['Claim'] = biblio_data

            if biblio_data is None:
                json_path = self.get_json_path(doc)
                self.stdout.write(
                    self.style.ERROR(f"Error: no biblio data in JSON: {json_path}"))
                IndexationError.objects.create(
                    app_id=doc['id'],
                    type='Other',
                    text='No biblio data in JSON',
                    json_path=json_path,
                    indexation_process=self.indexation_process
                )
            else:
                # Строка бюлетня ("10/2011" и т.д.)
                if biblio_data.get('I_43.D'):
                    i_43_d = biblio_data['I_43.D'][0]
                    bull_str = bulletin_get_number_with_year_by_date(i_43_d)
                    if bull_str:
                        biblio_data['I_43_bul_str'] = bull_str
                if biblio_data.get('I_45.D'):
                    i_45_d = biblio_data['I_45.D'][len(biblio_data['I_45.D']) - 1]
                    bull_str = bulletin_get_number_with_year_by_date(i_45_d)
                    if bull_str:
                        biblio_data['I_45_bul_str'] = bull_str

                # Обработка I_71 для избежания ошибки добавления в индекс ElasticSearch
                i_71 = biblio_data.get('I_71', [])
                if type(i_71) is dict:
                    i_71 = biblio_data['I_71']['I_71.N']
                biblio_data['I_71'] = i_71

                # Обработка I_72 для избежания ошибки добавления в индекс ElasticSearch
                for I_72 in biblio_data.get('I_72', []):
                    if I_72.get('I_72.N'):
                        I_72['I_72.N.E'] = I_72.pop('I_72.N')
                    if I_72.get('I_72.C'):
                        I_72['I_72.C.E'] = I_72.pop('I_72.C')

                # Обработка I_73 для избежания ошибки добавления в индекс ElasticSearch
                i_73 = biblio_data.get('I_73', [])
                if type(i_73) is dict:
                    i_73 = biblio_data['I_73']['I_73.N']

                for item_i_73 in i_73:
                    if item_i_73.get('I_73.N.U'):
                        item_i_73['I_73.N'] = item_i_73.pop('I_73.N.U')
                    if item_i_73.get('I_73.N.R'):
                        item_i_73['I_73.N'] = item_i_73.pop('I_73.N.R')
                    if item_i_73.get('I_73.N.E'):
                        item_i_73['I_73.N'] = item_i_73.pop('I_73.N.E')
                    if item_i_73.get('I_73.C.U'):
                        item_i_73['I_73.C'] = item_i_73.pop('I_73.C.U')
                    if item_i_73.get('I_73.C.R'):
                        item_i_73['I_73.C'] = item_i_73.pop('I_73.C.R')
                    if item_i_73.get('I_73.C.E'):
                        item_i_73['I_73.C'] = item_i_73.pop('I_73.C.E')
                biblio_data['I_73'] = i_73

                # Обработка I_98.Index
                if biblio_data.get('I_98.Index') is not None:
                    biblio_data['I_98_Index'] = biblio_data.pop('I_98.Index')

                # Признак что данные необходимо публиковать не в полном объёме
                if self.is_limited_publication:
                    res['Document']['is_limited'] = True

                    # Фильтрация библиографии
                    search_services.application_filter_limited_biblio_data(
                        doc['app_number'],
                        doc['obj_type_id'],
                        biblio_data,
                    )

                    # Удаление всех .pdf из каталога
                    delete_files_in_directory(self.get_doc_files_path(doc), '.pdf')

                # Состояние делопроизводства
                if data.get('DOCFLOW'):
                    res['DOCFLOW'] = data['DOCFLOW']

                # Оповещения
                if data.get('TRANSACTIONS'):
                    res['TRANSACTIONS'] = data['TRANSACTIONS']
                    # Дополнительное поле с датой бюлетня для поиска по ней
                    if type(res['TRANSACTIONS']['TRANSACTION']) is dict:
                        res['TRANSACTIONS']['TRANSACTION'] = [res['TRANSACTIONS']['TRANSACTION']]
                    for transaction in res['TRANSACTIONS']['TRANSACTION']:
                        bul_date = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', transaction['BULLETIN'])
                        try:
                            bul_date_groups = bul_date.groups()
                            d = f"{bul_date_groups[2]}-{bul_date_groups[1]}-{bul_date_groups[0]}"
                            transaction['BULLETIN_DATE'] = d
                        except (ValueError, IndexError, AttributeError):  # Строка бюлетня не содержит дату
                            pass

                # Поисковые данные (для сортировки и т.д.)
                res['search_data'] = {
                    'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                    'app_number': biblio_data.get('I_21'),
                    'app_date': biblio_data.get('I_22'),
                    'protective_doc_number': biblio_data.get('I_11'),
                    'rights_date': biblio_data.get('I_24') if biblio_data.get('I_24') != '1899-12-30' else None,
                    'applicant': [{'name': list(x.values())[0]} for x in biblio_data.get('I_71', [])],
                    'inventor': [{'name': list(x.values())[0]} for x in biblio_data.get('I_72', [])],
                    'owner': [{'name': list(x.values())[0]} if list(x.keys())[0] != 'EDRPOU'
                              else {'name': list(x.values())[1]} for x in biblio_data.get('I_73', [])],
                    'title': [list(x.values())[0] for x in biblio_data.get('I_54', [])]
                }

                # Представитель
                if biblio_data.get('I_74'):
                    res['search_data']['agent'] = [{'name': biblio_data['I_74']}]

                # Статус охранного документа (цвет)
                if res['search_data']['obj_state'] == 2:
                    res['search_data']['registration_status_color'] = get_registration_status_color(res)

                # Запись в индекс
                if search_services.application_inv_can_be_indexed(data):
                    self.write_to_es_index(doc, res)

    def process_invention_certificate(self, doc):
        """Добавляет документ типа "сертифікат додаткової охорони" в ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)

        if data is not None:
            owners = []
            for owner in data['Patent_Certificate'].get('I_73', []):
                owners.append({'name': owner['N.U']})

            # Поисковые данные (для сортировки и т.д.)
            data['search_data'] = {
                'obj_state': 2,
                'protective_doc_number': data['Patent_Certificate'].get('I_11'),
                'owner': owners,
                'title': data['Patent_Certificate'].get('I_95'),
                'registration_status_color': get_registration_status_color(data)
            }

            # Запись в индекс
            self.write_to_es_index(doc, data)

    def process_tm(self, doc):
        """Добавляет документ типа "знак для товаров и услуг" ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)

        res = {}
        if data is not None:
            # Секция Document
            res['Document'] = data.get('Document')

            # Fix новых данных
            res['Document']['filesPath'] = res['Document']['filesPath'].replace(
                'e:\\poznach_test_sis\\bear_tmpp_sis',
                '\\\\bear\\share'
            )
            if res['Document']['filesPath'][len(res['Document']['filesPath'])-1] != '\\':
                res['Document']['filesPath'] = f"{res['Document']['filesPath']}\\"

            # Секция TradeMark
            res['TradeMark'] = data.get('TradeMark')

            # Случай если секции PaymentDetails, DocFlow, Transactions не попали в секцию TradeMark
            if data.get('PaymentDetails'):
                res['TradeMark']['PaymentDetails'] = data.get('PaymentDetails')
            if data.get('DocFlow'):
                res['TradeMark']['DocFlow'] = data.get('DocFlow')
            if data.get('Transactions'):
                res['TradeMark']['Transactions'] = data.get('Transactions')

            # Форматирование даты публикации
            try:
                if res['TradeMark']['TrademarkDetails'].get('PublicationDetails', {}).get('Publication'):
                    try:
                        d = datetime.datetime.today().strptime(
                            res['TradeMark']['TrademarkDetails']['PublicationDetails']['Publication']['PublicationDate'],
                            '%d.%m.%Y'
                        )
                    except ValueError:
                        pass
                    else:
                        res['TradeMark']['TrademarkDetails']['PublicationDetails']['Publication']['PublicationDate'] \
                            = d.strftime('%Y-%m-%d')
                    res['TradeMark']['TrademarkDetails']['PublicationDetails'] = [
                        res['TradeMark']['TrademarkDetails']['PublicationDetails']['Publication']
                    ]
            except AttributeError:
                pass

            # Приведение номера бюлетня к формату "bul_num/YYYY"
            if res['TradeMark']['TrademarkDetails'].get('PublicationDetails'):
                for x in res['TradeMark']['TrademarkDetails']['PublicationDetails']:
                    if len(x.get('PublicationIdentifier')) < 6:
                        x['PublicationIdentifier'] = f"{x['PublicationIdentifier']}/{x['PublicationDate'][:4]}"

            # Fix оригинальных наименований и адресов заявителей
            if 'ApplicantDetails' in res['TradeMark']['TrademarkDetails']:
                for applicant in res['TradeMark']['TrademarkDetails']['ApplicantDetails']['Applicant']:
                    formatted_name_address = applicant['ApplicantAddressBook']['FormattedNameAddress']
                    is_ua = formatted_name_address['Address']['AddressCountryCode'] == 'UA'
                    if 'FreeFormatAddressLineOriginal' in formatted_name_address['Address']['FreeFormatAddress']:
                        if is_ua or formatted_name_address['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal'] == '':
                            del formatted_name_address['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal']
                    if 'FreeFormatNameLineOriginal' in formatted_name_address['Address']['FreeFormatAddress']:
                        if is_ua or formatted_name_address['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal'] == '':
                            del formatted_name_address['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal']
                    if 'FreeFormatNameLineOriginal' in formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails']:
                        if is_ua or \
                                formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails'][
                                    'FreeFormatNameLineOriginal'] == '':
                            del formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails'][
                                'FreeFormatNameLineOriginal']

            # Fix оригинальных наименований и адресов владельцев
            if 'HolderDetails' in res['TradeMark']['TrademarkDetails']:
                for holder in res['TradeMark']['TrademarkDetails']['HolderDetails']['Holder']:
                    formatted_name_address = holder['HolderAddressBook']['FormattedNameAddress']
                    is_ua = formatted_name_address['Address']['AddressCountryCode'] == 'UA'
                    if 'FreeFormatAddressLineOriginal' in formatted_name_address['Address']['FreeFormatAddress']:
                        if is_ua or formatted_name_address['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal'] == '':
                            del formatted_name_address['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal']
                    if 'FreeFormatNameLineOriginal' in formatted_name_address['Address']['FreeFormatAddress']:
                        if is_ua or formatted_name_address['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal'] == '':
                            del formatted_name_address['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal']
                    if 'FreeFormatNameLineOriginal' in formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails']:
                        if is_ua or \
                                formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails'][
                                    'FreeFormatNameLineOriginal'] == '':
                            del formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails'][
                                'FreeFormatNameLineOriginal']

            # Признак что данные необходимо публиковать не в полном объёме
            if self.is_limited_publication:
                res['Document']['is_limited'] = True
                if 'ApplicantDetails' in res['TradeMark']['TrademarkDetails']:
                    del res['TradeMark']['TrademarkDetails']['ApplicantDetails']
                if 'HolderDetails' in res['TradeMark']['TrademarkDetails']:
                    del res['TradeMark']['TrademarkDetails']['HolderDetails']
                if 'CorrespondenceAddress' in res['TradeMark']['TrademarkDetails']:
                    del res['TradeMark']['TrademarkDetails']['CorrespondenceAddress']
                if 'MarkImageDetails' in res['TradeMark']['TrademarkDetails']:
                    if 'MarkImageColourClaimedText' in res['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']:
                        del res['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']['MarkImageColourClaimedText']
                    del res['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']['MarkImageFilename']

            # Список заявителей для быстрого поиска по наименованию
            applicants_search_data = []
            if res['TradeMark']['TrademarkDetails'].get('ApplicantDetails'):
                for applicant in res['TradeMark']['TrademarkDetails']['ApplicantDetails']['Applicant']:
                    applicants_search_data.append(
                        {
                            'name': applicant['ApplicantAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                                'FreeFormatNameDetails']['FreeFormatNameLine']
                        }
                    )
                    if 'FreeFormatNameLineOriginal' in applicant['ApplicantAddressBook'][
                        'FormattedNameAddress']['Name']['FreeFormatName']['FreeFormatNameDetails']:
                        applicants_search_data.append(
                            {
                                'name': applicant['ApplicantAddressBook']['FormattedNameAddress']['Name'][
                                    'FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLineOriginal']
                            }
                        )

            # Список владельцев для быстрого поиска по наименованию
            holders_search_data = []
            if res['TradeMark']['TrademarkDetails'].get('HolderDetails'):
                for holder in res['TradeMark']['TrademarkDetails']['HolderDetails']['Holder']:
                    holders_search_data.append(
                        {
                            'name': holder['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                                'FreeFormatNameDetails']['FreeFormatNameLine']
                        }
                    )
                    if 'FreeFormatNameLineOriginal' in holder['HolderAddressBook']['FormattedNameAddress']['Name'][
                        'FreeFormatName']['FreeFormatNameDetails']:
                        holders_search_data.append(
                            {
                                'name': holder['HolderAddressBook']['FormattedNameAddress']['Name'][
                                    'FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLineOriginal']
                            }
                        )

            # Поле 441 (дата опубликования заявки)
            if res['TradeMark']['TrademarkDetails'].get('Code_441'):
                EBulletinData.objects.update_or_create(
                    app_number=res['TradeMark']['TrademarkDetails'].get('ApplicationNumber'),
                    unit_id=1,
                    defaults={
                        'publication_date': datetime.datetime.strptime(
                            res['TradeMark']['TrademarkDetails']['Code_441'],
                            '%Y-%m-%d'
                        )
                    }
                )
            else:
                e_bulletin_data = EBulletinData.objects.filter(
                    app_number=res['TradeMark']['TrademarkDetails'].get('ApplicationNumber')
                ).first()
                if e_bulletin_data:
                    res['TradeMark']['TrademarkDetails']['Code_441'] = e_bulletin_data.publication_date.strftime('%Y-%m-%d')

            # Поисковые данные (для сортировки и т.д.)
            res['search_data'] = {
                'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                'app_number': res['TradeMark']['TrademarkDetails'].get('ApplicationNumber'),
                'protective_doc_number': res['TradeMark']['TrademarkDetails'].get('RegistrationNumber'),
                'rights_date': res['TradeMark']['TrademarkDetails'].get('RegistrationDate'),
                'applicant': applicants_search_data,
                'owner': holders_search_data
                if res['TradeMark']['TrademarkDetails'].get('HolderDetails') else None,
                'title': ', '.join([x['#text'] for x in res['TradeMark']['TrademarkDetails']['WordMarkSpecification'][
                    'MarkSignificantVerbalElement']])
                if res['TradeMark']['TrademarkDetails'].get('WordMarkSpecification') else '',
            }

            if res['TradeMark']['TrademarkDetails'].get('ApplicationDate'):
                res['search_data']['app_date'] = res['TradeMark']['TrademarkDetails']['ApplicationDate']
            else:
                if doc['app_date']:
                    res['search_data']['app_date'] = doc['app_date'].strftime('%Y-%m-%d')
                else:
                    res['search_data']['app_date'] = doc['app_input_date'].strftime('%Y-%m-%d')

            # Представитель
            res['search_data']['agent'] = []
            for representer in res['TradeMark']['TrademarkDetails'].get('RepresentativeDetails', {}).get('Representative',
                                                                                                   []):
                name = representer['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                    'FreeFormatNameDetails']['FreeFormatNameDetails']['FreeFormatNameLine']
                address = representer['RepresentativeAddressBook']['FormattedNameAddress']['Address'][
                    'FreeFormatAddress']['FreeFormatAddressLine']
                res['search_data']['agent'].append({'name': f"{name}, {address}"})

            # Статус охранного документа (цвет)
            if res['search_data']['obj_state'] == 2:
                res['search_data']['registration_status_color'] = get_registration_status_color(res)

            if res['TradeMark']['TrademarkDetails'].get('stages'):
                res['TradeMark']['TrademarkDetails']['stages'] = res['TradeMark']['TrademarkDetails']['stages'][::-1]
                # Если есть охранный документ, то все стадии д.б. done
                if 'RegistrationNumber' in res['TradeMark']['TrademarkDetails']:
                    for stage in res['TradeMark']['TrademarkDetails']['stages']:
                        stage['status'] = 'done'

            # Fix новых данных
            if res['TradeMark']['TrademarkDetails'].get(
                    'AssociatedRegistrationApplicationDetails', {}
            ).get(
                'AssociatedRegistrationApplication', {}
            ).get(
                'AssociatedRegistrationDetails', {}
            ).get(
                'DivisionalApplication'
            ):
                for app in res['TradeMark']['TrademarkDetails']['AssociatedRegistrationApplicationDetails'][
                    'AssociatedRegistrationApplication']['AssociatedRegistrationDetails']['DivisionalApplication']:
                    try:
                        app['AssociatedRegistration']['AssociatedRegistrationDate'] = datetime.datetime.strptime(
                            app['AssociatedRegistration']['AssociatedRegistrationDate'], '%d.%m.%Y'
                        ).strftime('%Y-%m-%d')
                    except:
                        pass

            # Fix новых данных
            if res['TradeMark']['TrademarkDetails'].get('TerminationDate'):
                try:
                    res['TradeMark']['TrademarkDetails']['TerminationDate'] = datetime.datetime.strptime(
                        res['TradeMark']['TrademarkDetails']['TerminationDate'], '%d.%m.%Y'
                    ).strftime('%Y-%m-%d')
                except:
                    pass

            # Fix ExhibitionPriorityDetails
            if 'ExhibitionPriorityDetails' in res['TradeMark']['TrademarkDetails'] \
                    and type(res['TradeMark']['TrademarkDetails']['ExhibitionPriorityDetails']) == list:
                res['TradeMark']['TrademarkDetails']['ExhibitionPriorityDetails'] = {
                    'ExhibitionPriority': res['TradeMark']['TrademarkDetails']['ExhibitionPriorityDetails']
                }

            # fix оповещений
            if res['TradeMark'].get('Transactions', {}).get('Transaction'):
                # Удаление чужих оповещений
                res['TradeMark']['Transactions']['Transaction'] = list(filter(
                    lambda x: x.get('@registrationNumber') == res['TradeMark']['TrademarkDetails'].get('RegistrationNumber'),
                    res['TradeMark']['Transactions']['Transaction']
                ))

                for transaction in res['TradeMark']['Transactions']['Transaction']:
                    # fix структуры
                    if 'TransactionBody' in transaction:
                        if 'PublicationDate' in transaction['TransactionBody'] \
                                or 'PublicationNumber' in transaction['TransactionBody']:
                            transaction['TransactionBody']['PublicationDetails'] = {
                                'Publication': {
                                    'PublicationDate': transaction['TransactionBody'].pop('PublicationDate', None),
                                    'PublicationNumber': transaction['TransactionBody'].pop('PublicationNumber', None),
                                }
                            }

                        # fix дат
                        try:
                            d = transaction['TransactionBody']['PublicationDetails']['Publication'][
                                'PublicationDate']
                            transaction['TransactionBody']['PublicationDetails']['Publication'][
                                'PublicationDate'] = datetime.datetime.strptime(d, '%d.%m.%Y').strftime('%Y-%m-%d')
                        except:
                            pass
                        try:
                            d = transaction['TransactionBody']['RegisterDate']
                            transaction['TransactionBody']['RegisterDate'] = datetime.datetime.strptime(
                                d, '%d.%m.%Y'
                            ).strftime('%Y-%m-%d')
                        except:
                            pass

            # Fix id_doc_cead
            self.fix_id_doc_cead(res['TradeMark'].get('DocFlow', {}).get('Documents', []))

            # Проверка, содержит ли изображение недопустимые символы
            if search_services.application_tm_censored_image_in_data(res):
                self._censor_tm_image(doc, res)
            else:
                # Исправляет название файла на диске, если оно отлично от номера свидетельства или заявки
                self._fix_tm_image(doc, res)

            # Запись в индекс
            if search_services.application_tm_can_be_indexed(data):
                self.write_to_es_index(doc, res)

    def process_id(self, doc):
        """Добавляет документ типа "пром. образец" ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)

        res = {}
        if data is not None:
            # Секция Document
            res['Document'] = data.get('Document')

            # fix новых данных
            if res['Document']['filesPath'][len(res['Document']['filesPath'])-1] != '\\':
                res['Document']['filesPath'] = f"{res['Document']['filesPath']}\\"

            # Секция Design
            res['Design'] = data.get('Design')

            # Формат МКПЗ
            for item in res['Design']['DesignDetails'].get('IndicationProductDetails', {}):
                cl = item.get('Class')
                if cl:
                    cl = cl.replace('.', '-')
                    cl_l = cl.split('-')
                    if len(cl_l[1]) == 1:
                        cl_l[1] = f"0{cl_l[1]}"
                    item['Class'] = '-'.join(cl_l)

            # Случай если секции PaymentDetails, DocFlow, Transactions не попали в секцию Design
            if data.get('PaymentDetails'):
                res['Design']['PaymentDetails'] = data.get('PaymentDetails')
            if data.get('DocFlow'):
                res['Design']['DocFlow'] = data.get('DocFlow')
            if data.get('Transactions'):
                res['Design']['Transactions'] = data.get('Transactions')

            # Приведение номеря бюлетня к формату "bul_num/YYYY"
            if res['Design']['DesignDetails'].get('RecordPublicationDetails'):
                for x in res['Design']['DesignDetails']['RecordPublicationDetails']:
                    if len(x.get('PublicationIdentifier')) < 6:
                        x['PublicationIdentifier'] = f"{x['PublicationIdentifier']}/{x['PublicationDate'][:4]}"

            # Признак что данные необходимо публиковать не в полном объёме
            if self.is_limited_publication:
                res['Document']['is_limited'] = True
                if 'ApplicantDetails' in res['Design']['DesignDetails']:
                    del res['Design']['DesignDetails']['ApplicantDetails']
                if 'DesignerDetails' in res['Design']['DesignDetails']:
                    del res['Design']['DesignDetails']['DesignerDetails']
                if 'HolderDetails' in res['Design']['DesignDetails']:
                    del res['Design']['DesignDetails']['HolderDetails']
                if 'CorrespondenceAddress' in res['Design']['DesignDetails']:
                    del res['Design']['DesignDetails']['CorrespondenceAddress']
                if 'DesignSpecimenDetails' in res['Design']['DesignDetails']:
                    del res['Design']['DesignDetails']['DesignSpecimenDetails']
                # Удаление всех .jpeg, .jpg, .png, .tiff из каталога
                exts = ('.jpeg', '.jpg', '.png', '.tiff')
                directory = self.get_doc_files_path(doc)
                for ext in exts:
                    delete_files_in_directory(directory, ext)
                    delete_files_in_directory(directory, ext.upper())

            applicant = None
            if res['Design']['DesignDetails'].get('ApplicantDetails'):
                applicant = [{'name': x['ApplicantAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                                 'FreeFormatNameDetails']['FreeFormatNameLine']} for x in
                             res['Design']['DesignDetails']['ApplicantDetails']['Applicant']]

            # Поисковые данные (для сортировки и т.д.)
            res['search_data'] = {
                'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                'app_number': res['Design']['DesignDetails'].get('DesignApplicationNumber'),
                'protective_doc_number': res['Design']['DesignDetails'].get('RegistrationNumber'),
                'rights_date': res['Design']['DesignDetails'].get('RecordEffectiveDate'),
                'applicant': applicant,

                'inventor': [{'name': x['DesignerAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine']} for x in
                          res['Design']['DesignDetails']['DesignerDetails']['Designer']]
                if res['Design']['DesignDetails'].get('DesignerDetails') else None,

                'title': res['Design']['DesignDetails'].get('DesignTitle')
            }

            res['search_data']['owner'] = []
            if res['Design']['DesignDetails'].get('HolderDetails'):
                for x in res['Design']['DesignDetails']['HolderDetails']['Holder']:
                    try:
                        res['search_data']['owner'].append({
                            'name': x['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                                  'FreeFormatNameDetails']['FreeFormatNameLine']
                        })
                    except KeyError:
                        pass

            if res['Design']['DesignDetails'].get('DesignApplicationDate'):
                res['search_data']['app_date'] = res['Design']['DesignDetails']['DesignApplicationDate']
            else:
                if doc['app_date']:
                    res['search_data']['app_date'] = doc['app_date'].strftime('%Y-%m-%d')
                else:
                    res['search_data']['app_date'] = doc['app_input_date'].strftime('%Y-%m-%d')

            # Представитель
            res['search_data']['agent'] = []
            for representer in res['Design']['DesignDetails'].get('RepresentativeDetails', {}).get('Representative', []):
                name = representer['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                        'FreeFormatNameDetails']['FreeFormatNameLine']
                address = representer['RepresentativeAddressBook']['FormattedNameAddress']['Address'][
                    'FreeFormatAddress']['FreeFormatAddressLine']
                res['search_data']['agent'].append({'name': f"{name}, {address}"})

            # Статус охранного документа (цвет)
            if res['search_data']['obj_state'] == 2:
                res['search_data']['registration_status_color'] = get_registration_status_color(res)

            if res['Design']['DesignDetails'].get('stages'):
                res['Design']['DesignDetails']['stages'] = res['Design']['DesignDetails']['stages'][::-1]
                # Если есть охранный документ, то все стадии д.б. done
                if 'RegistrationNumber' in res['Design']['DesignDetails']:
                    for stage in res['Design']['DesignDetails']['stages']:
                        stage['status'] = 'done'

            # fix priority date
            try:
                if res['Design']['DesignDetails'].get('PriorityDetails', {}).get('Priority'):
                    for item in res['Design']['DesignDetails']['PriorityDetails']['Priority']:
                        if not item['PriorityDate']:
                            del item['PriorityDate']
            except AttributeError:
                pass

            # fix оповещений
            if res['Design'].get('Transactions', {}).get('Transaction'):
                # Удаление чужих оповещений
                res['Design']['Transactions']['Transaction'] = list(filter(
                    lambda x: x.get('@registrationNumber') == res['Design']['DesignDetails'].get('RegistrationNumber'),
                    res['Design']['Transactions']['Transaction']
                ))

                # fix дат
                for transaction in res['Design']['Transactions']['Transaction']:
                    try:
                        d = transaction['TransactionBody']['PublicationDetails']['Publication']['PublicationDate']
                        transaction['TransactionBody']['PublicationDetails']['Publication'][
                            'PublicationDate'] = datetime.datetime.strptime(d, '%d.%m.%Y').strftime('%Y-%m-%d')
                    except:
                        pass

            # Fix id_doc_cead
            self.fix_id_doc_cead(res['Design'].get('DocFlow', {}).get('Documents', []))

            # Запись в индекс
            if search_services.application_id_can_be_indexed(data):
                self.write_to_es_index(doc, res)

    def process_kzpt(self, doc):
        """Добавляет документ типа "географічне зазначення" ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)

        res = {}
        if data is not None:
            # Секция Document
            res['Document'] = data.get('Document')

            # Секция Geo
            res['Geo'] = data.get('Geo')

            # Fix ProductDesc
            if 'ProductDescription' in res['Geo']['GeoDetails']:
                res['Geo']['GeoDetails']['ProductDesc'] = res['Geo']['GeoDetails'].pop('ProductDescription')

            applicant = None
            if res['Geo']['GeoDetails'].get('ApplicantDetails'):
                applicant = [{'name': x['ApplicantAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                    'FreeFormatNameDetails']['FreeFormatNameLine']} for x in
                             res['Geo']['GeoDetails']['ApplicantDetails']['Applicant']]

            # Поисковые данные (для сортировки и т.д.)
            res['search_data'] = {
                'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                'app_number': res['Geo']['GeoDetails'].get('ApplicationNumber'),
                'app_date': res['Geo']['GeoDetails'].get('ApplicationDate'),
                'protective_doc_number': res['Geo']['GeoDetails'].get('RegistrationNumber'),
                'rights_date': res['Geo']['GeoDetails'].get('RegistrationDate'),
                'applicant': applicant,
                'owner': [{'name': x['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine']} for x in
                          res['Geo']['GeoDetails']['HolderDetails']['Holder']]
                if res['Geo']['GeoDetails'].get('HolderDetails') else None,

                'agent': [{'name': x['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine']} for x in
                          res['Geo']['GeoDetails']['RepresentativeDetails']['Representative']]
                if res['Geo']['GeoDetails'].get('RepresentativeDetails') else None,

                'title': res['Geo']['GeoDetails'].get('Indication'),
            }

            # Статус охранного документа (цвет)
            if res['search_data']['obj_state'] == 2:
                res['search_data']['registration_status_color'] = get_registration_status_color(res)

            # Запись в индекс
            self.write_to_es_index(doc, res)

            # Запись в таблицу с 441 кодом (для бюллетеня)
            if 'ApplicationPublicationDetails' in res['Geo']['GeoDetails']:
                EBulletinData.objects.update_or_create(
                    app_number=res['Geo']['GeoDetails'].get('ApplicationNumber'),
                    unit_id=3,
                    defaults={
                        'publication_date': res['Geo']['GeoDetails']['ApplicationPublicationDetails']['PublicationDate']
                    }
                )

    def process_madrid_tm(self, doc):
        """Обрабатывает документ типа "мадридские тм"."""
        # Считывание данных из файла
        data_from_json = self.get_data_from_json(doc)

        if data_from_json is not None:
            # Парсинг дат
            date_keys = ['@EXPDATE', '@NOTDATE', '@REGEDAT', '@REGRDAT', '@INTREGD']
            for i in date_keys:
                if data_from_json.get(i):
                    data_from_json[i] = datetime.datetime.strptime(data_from_json[i], '%Y%m%d').strftime('%Y-%m-%d')
            if data_from_json.get('ENN', {}).get('@PUBDATE'):
                data_from_json['ENN']['@PUBDATE'] = datetime.datetime.strptime(
                    data_from_json['ENN']['@PUBDATE'], '%Y%m%d'
                ).strftime('%Y-%m-%d')
            if data_from_json.get('BASGR', {}).get('BASAPPGR', {}).get('BASAPPD'):
                data_from_json['BASGR']['BASAPPGR']['BASAPPD'] = datetime.datetime.strptime(
                    data_from_json['BASGR']['BASAPPGR']['BASAPPD'], '%Y%m%d'
                ).strftime('%Y-%m-%d')
            if data_from_json.get('PRIGR', {}).get('PRIAPPD', {}):
                data_from_json['PRIGR']['PRIAPPD'] = datetime.datetime.strptime(
                    data_from_json['PRIGR']['PRIAPPD'], '%Y%m%d'
                ).strftime('%Y-%m-%d')

            # Данные для записи в ElasticSearch
            data = {
                'Document': {
                    'idObjType': doc['obj_type_id'],
                    'filesPath': doc['files_path']
                },
                'MadridTradeMark': {
                    'TradeMarkDetails': data_from_json
                },
                'search_data': {
                    'app_number': doc['app_number'],
                    'protective_doc_number': doc['registration_number'],
                    'obj_state': 2,
                    'rights_date': data_from_json.get('@INTREGD'),
                    'owner': [{'name': data_from_json.get('HOLGR', {}).get('NAME', {}).get('NAMEL')}],
                    'agent': [{'name': data_from_json['REPGR']['NAME']['NAMEL']}] if data_from_json.get('REPGR', {}).get('NAME', {}).get('NAMEL') else None,
                    'title': data_from_json.get('IMAGE', {}).get('@TEXT'),
                }
            }

            # Поле 441 (дата опубликования заявки)
            try:
                app = IpcAppList.objects.filter(
                    obj_type_id=9,  # registration_date у заявки с этим obj_type_id и будет 441-м кодом
                    app_number=doc['app_number']
                ).first()
                data['MadridTradeMark']['TradeMarkDetails']['Code_441'] = app.registration_date.strftime('%Y-%m-%d')
            except AttributeError:
                data['MadridTradeMark']['TradeMarkDetails']['Code_441'] = doc['registration_date'].strftime('%Y-%m-%d')

            # Поле 450 (Дата публікації відомостей про міжнародну реєстрацію та номер бюлетеню Міжнародного бюро ВОІВ)
            if doc['obj_type_id'] == 14:
                '''Если это "Міжнародна реєстрація торговельної марки, що зареєстрована в Україні", которая появляется
                позже чем "Міжнародна реєстрація торговельної марки з поширенням на територію України" с тем же номером,
                то необхожимо обновить 450-й код у "Міжнародна реєстрація торговельної марки з поширенням на територію України"'''
                q = Q(
                    'bool',
                    must=[
                        Q('match', Document__idObjType=9),
                        Q('match', search_data__protective_doc_number=doc['registration_number']),
                    ],
                )
                s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.es).query(q).execute()
                if s:
                    hit = s[0].to_dict()
                    hit['MadridTradeMark']['TradeMarkDetails']['ENN'] = data['MadridTradeMark']['TradeMarkDetails']['ENN']
                    self.es.index(index=settings.ELASTIC_INDEX_NAME,
                                  doc_type='_doc',
                                  id=s[0].meta.id,
                                  body=hit,
                                  request_timeout=30)
            elif doc['obj_type_id'] == 9:
                '''Если это "Міжнародна реєстрація торговельної марки з поширенням на територію України", 
                то надо проверить есть ли аналогичная "Міжнародна реєстрація торговельної марки, що зареєстрована в Україні"
                и взять у неё 450 код.'''
                q = Q(
                    'bool',
                    must=[
                        Q('match', Document__idObjType=14),
                        Q('match', search_data__protective_doc_number=doc['registration_number']),
                    ],
                )
                s = Search(index=settings.ELASTIC_INDEX_NAME).using(self.es).query(q).execute()
                if s:
                    hit = s[0].to_dict()
                    data['MadridTradeMark']['TradeMarkDetails']['ENN'] = hit['MadridTradeMark']['TradeMarkDetails']['ENN']

            # Запись в индекс
            self.write_to_es_index(doc, data)

            # Запись в БД для бюлетня
            EBulletinData.objects.update_or_create(
                app_number=doc['registration_number'],
                unit_id=2,
                defaults={'publication_date': data['MadridTradeMark']['TradeMarkDetails']['Code_441']}
            )

    def process_cr(self, doc):
        """Добавляет документ типа "авторское право" в ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)
        res = {}
        if data is not None:
            # Секция Document
            res['Document'] = data.get('Document')

            if doc['obj_type_id'] in (10, 13):  # Свидетельства
                # Секция Certificate
                res['Certificate'] = data.get('Certificate')
                # Признак что данные необходимо публиковать не в полном объёме
                if self.is_limited_publication:
                    res['Document']['is_limited'] = True
                    search_services.application_filter_limited_biblio_data(
                        doc['app_number'],
                        doc['obj_type_id'],
                        res['Certificate']['CopyrightDetails']
                    )
                cr_data = res['Certificate']['CopyrightDetails']

            else:  # Договоры
                # Секция Decision
                res['Decision'] = data.get('Decision')
                # Признак что данные необходимо публиковать не в полном объёме
                if search_services.application_is_limited_publication(
                        doc['app_number'],
                        res['Document']['idObjType']
                ):
                    res['Document']['is_limited'] = True
                    limited_data = {}
                    if 'RegistrationNumber' in res['Decision']['DecisionDetails']:
                        limited_data['RegistrationNumber'] = res['Decision']['DecisionDetails']['RegistrationNumber']
                    if 'RegistrationDate' in res['Decision']['DecisionDetails']:
                        limited_data['RegistrationDate'] = res['Decision']['DecisionDetails']['RegistrationDate']
                    if 'PublicationDetails' in res['Decision']['DecisionDetails']:
                        limited_data['PublicationDetails'] = res['Decision']['DecisionDetails']['PublicationDetails']
                    if 'PublicationDetails' in res['Decision']['DecisionDetails']:
                        limited_data['PublicationDetails'] = res['Decision']['DecisionDetails']['PublicationDetails']
                    if 'Name' in res['Decision']['DecisionDetails']:
                        limited_data['Name'] = res['Decision']['DecisionDetails']['Name']
                    if 'NameShort' in res['Decision']['DecisionDetails']:
                        limited_data['NameShort'] = res['Decision']['DecisionDetails']['NameShort']
                    res['Decision']['DecisionDetails'] = limited_data
                cr_data = res['Decision']['DecisionDetails']

            # fix PublicationDate
            if cr_data.get('PublicationDetails', {}).get('Publication', {}).get('PublicationDate'):
                d = cr_data['PublicationDetails']['Publication']['PublicationDate']
                cr_data['PublicationDetails']['Publication']['PublicationDate'] = datetime.datetime.strptime(
                    d, '%d.%m.%Y'
                ).strftime('%Y-%m-%d')

            # Поисковые данные (для сортировки и т.д.)
            res['search_data'] = {
                'obj_state': 2,
                'app_number': cr_data.get('ApplicationNumber'),
                'app_date': cr_data.get('ApplicationDate'),
                'protective_doc_number': cr_data.get('RegistrationNumber'),
                'rights_date': cr_data.get('RegistrationDate'),
                'owner': [{'name': x['AuthorAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine']} for x in
                          cr_data['AuthorDetails']['Author']]
                if cr_data.get('AuthorDetails', {}).get('Author') else None,

                'title': cr_data.get('Name'),
                'registration_status_color': 'red' if res['Document']['RegistrationStatus'] == 'Реєстрація недійсна' else 'green',
            }
            # Запись в индекс
            self.write_to_es_index(doc, res)

    def _fix_tm_image(self, doc: dict, body: dict) -> None:
        """Исправляет название файла на диске, если оно отличается от того что в исходном JSON."""
        try:
            image_name_json = body['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']['MarkImageFilename']
        except KeyError:
            pass
        else:
            file_path = self.get_doc_files_path(doc)
            image_json_path = os.path.join(file_path, image_name_json)
            if not os.path.exists(image_json_path):
                # Получение текущего имени файла
                data = search_services.application_get_app_elasticsearch_data(doc['id'])
                if data:
                    image_name_old = data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']['MarkImageFilename']
                    image_old_path = os.path.join(file_path, image_name_old)
                    try:
                        shutil.copyfile(image_old_path, image_json_path)
                    except FileNotFoundError:
                        pass

    def _censor_tm_image(self, doc: dict, body: dict) -> None:
        """Подменяет файл с изображением на изображение-заглушку."""
        image_name_json = body['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']['MarkImageFilename']
        file_path = self.get_doc_files_path(doc)
        image_json_path = os.path.join(file_path, image_name_json)
        censored_image_path = os.path.join(settings.BASE_DIR, 'assets', 'img', 'censored.jpg')
        shutil.copyfile(censored_image_path, image_json_path)

    def write_to_es_index(self, doc, body):
        """Записывает в индекс ES."""
        try:
            self.es.index(index=settings.ELASTIC_INDEX_NAME, doc_type='_doc', id=doc['id'], body=body,
                          request_timeout=30)
        except elasticsearch_exceptions.RequestError as e:
            json_path = self.get_json_path(doc)
            self.stdout.write(self.style.ERROR(f"ElasticSearch RequestError: {e}: {json_path}"))
            IndexationError.objects.create(
                app_id=doc['id'],
                type='ElasticSearch RequestError',
                text=e,
                json_path=json_path,
                indexation_process=self.indexation_process
            )
        except elasticsearch_exceptions.ConnectionTimeout as e:
            json_path = self.get_json_path(doc)
            self.stdout.write(self.style.ERROR(f"ElasticSearch ConnectionTimeout: {e}: {json_path}"))
            IndexationError.objects.create(
                app_id=doc['id'],
                type='ElasticSearch ConnectionTimeout',
                text=e,
                json_path=json_path,
                indexation_process=self.indexation_process
            )
        else:
            # Пометка в БД что этот документ проиндексирован и обновление времени индексации
            IpcAppList.objects.filter(id=doc['id']).update(
                elasticindexed=1,
                last_indexation_date=timezone.now(),
                is_limited=self.is_limited_publication
            )

    def fill_notification_date(self):
        """Заполняет поле NotificationDate в таблице IPC_AppList."""
        app_list = IpcAppList.objects.filter(obj_type__id__in=(1, 2))
        registration_date__max = app_list.aggregate(Max('registration_date'))['registration_date__max']
        q = Q(
            "nested",
            path="TRANSACTIONS.TRANSACTION",
            query=Q(
                "query_string",
                query=registration_date__max.date(),
                default_field="TRANSACTIONS.TRANSACTION.BULLETIN_DATE",
            )
        )
        s = Search(using=self.es, index=settings.ELASTIC_INDEX_NAME).query(q).source(False)
        total = s.count()
        s = s[0:total]
        results = s.execute()
        ids = []
        for res in results:
            ids.append(res.meta.id)
        IpcAppList.objects.filter(id__in=ids).update(notification_date=registration_date__max)

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        # Получение документов для индексации
        documents = IpcAppList.objects.exclude(
            Q_db(registration_date__gte=timezone.now()) | Q_db(app_number__in=[
                'm202006737', 'm202006738', 'm202021203', 'm202021202', 'm202021173', 'm202020602',
                'm202020603', 'm202020601', 'm202020630', 'm202009450', 'm202009453', 'm202009452'])
        ).values(
            'id',
            'files_path',
            'obj_type_id',
            'registration_number',
            'registration_date',
            'app_number',
            'app_date',
            'app_input_date',
        )
        # Фильтрация по параметрам командной строки
        if not options['ignore_indexed']:
            documents = documents.filter(elasticindexed=0)
        if options['id']:
            documents = documents.filter(id=options['id'])
        if options['obj_type']:
            documents = documents.filter(obj_type=options['obj_type'])
        if options['status']:
            status = int(options['status'])
            if status == 1:
                documents = documents.filter(registration_number__isnull=True)
            elif status == 2:
                documents = documents.exclude(registration_number__isnull=True)

        # Создание процесса индексации в БД
        self.indexation_process = IndexationProcess.objects.create(
            begin_date=timezone.now(),
            not_indexed_count=documents.count()
        )

        self.stdout.write(self.style.SUCCESS('The list of documents has been successfully received.'))

        for doc in documents:
            self.is_limited_publication = search_services.application_is_limited_publication(
                doc['app_number'], doc['obj_type_id']
            )

            # Изобретения, полезные модели, топографии интегральных микросхем
            if doc['obj_type_id'] in (1, 2, 3):
                self.process_inv_um_ld(doc)
            # Знаки для товаров и услуг
            elif doc['obj_type_id'] == 4:
                self.process_tm(doc)
            # КЗПТ
            elif doc['obj_type_id'] == 5:
                self.process_kzpt(doc)
            # Пром. образцы
            elif doc['obj_type_id'] == 6:
                self.process_id(doc)
            # Мадрид ТМ
            elif doc['obj_type_id'] in (9, 14):
                self.process_madrid_tm(doc)
            # Авторское право
            elif doc['obj_type_id'] in (10, 11, 12, 13):
                self.process_cr(doc)
            elif doc['obj_type_id'] == 16:
                self.process_invention_certificate(doc)
            # Увеличение счётчика обработанных документов
            self.indexation_process.processed_count += 1
            self.indexation_process.save()

            # Удаление JSON
            # try:
            #     os.remove(self.get_json_path(doc))
            # except (FileNotFoundError, PermissionError):
            #     pass

        # Время окончания процесса индексации и сохранение данных процесса индексации
        self.indexation_process.finish_date = timezone.now()

        qs = Q('query_string', query='*')

        # Не включать в список результатов заявки, по которым выдан патент
        qs = filter_bad_apps(qs)

        # Количество документов в индексе
        s = Search(using=self.es, index=settings.ELASTIC_INDEX_NAME).query(qs)
        self.indexation_process.documents_in_index = s.count()
        self.indexation_process.save()

        # Заполнение поля NotificationDate в таблице IPC_AppList
        self.fill_notification_date()

        self.stdout.write(self.style.SUCCESS('Finished'))
