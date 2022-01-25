from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.db.models import Max
from django.utils import timezone
from elasticsearch import Elasticsearch, exceptions as elasticsearch_exceptions
from elasticsearch_dsl import Search, Q
from apps.search.models import IpcAppList, IndexationError, IndexationProcess
from apps.bulletin.models import EBulletinData, ClListOfficialBulletinsIp
from ...utils import get_registration_status_color, filter_bad_apps
import json
import os
import datetime
import uuid


class Command(BaseCommand):
    help = 'Adds or updates documents in ElasticSearch index.'
    es = None
    indexation_process = None

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

        # Случай если охранные документы на ТМ имеют название заявки
        if not os.path.exists(json_path) and doc['obj_type_id'] in (4, 6):
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
            f = open(json_path, 'r', encoding='utf-8')
            try:
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
                if res['Document']['idObjType'] == 1 and data.get('Claim', {}).get('I_43.D'):  # Заявки на изобретения
                    i_43_d = data['Claim']['I_43.D'][0]
                    try:
                        bulletin = ClListOfficialBulletinsIp.objects.get(bul_date=i_43_d)
                    except ClListOfficialBulletinsIp.DoesNotExist:
                        pass
                    else:
                        bull_str = f"{bulletin.bul_number}/{bulletin.bul_date.year}"
                        data['Claim']['I_43_bul_str'] = bull_str
                elif data.get('Patent', {}).get('I_45.D'):  # Патенты на изобретения, пол. модели, топографии
                    i_45_d = data['Patent']['I_45.D'][len(data['Patent']['I_45.D']) - 1]
                    try:
                        bulletin = ClListOfficialBulletinsIp.objects.get(bul_date=i_45_d)
                    except ClListOfficialBulletinsIp.DoesNotExist:
                        pass
                    else:
                        bull_str = f"{bulletin.bul_number}/{bulletin.bul_date.year}"
                        data['Patent']['I_45_bul_str'] = bull_str

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
                        bulletin = transaction['BULLETIN'].split(', ')
                        try:
                            transaction['BULLETIN_DATE'] = datetime.datetime.strptime(
                                bulletin[1], '%d.%m.%Y'
                            ).strftime('%Y-%m-%d')
                        except (ValueError, IndexError):  # Строка бюлетня не содержит дату
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
                self.write_to_es_index(doc, res)

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

            applicant = None
            if res['TradeMark']['TrademarkDetails'].get('ApplicantDetails'):
                applicant = [{'name': x['ApplicantAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                                 'FreeFormatNameDetails']['FreeFormatNameLine']} for x in
                             res['TradeMark']['TrademarkDetails']['ApplicantDetails']['Applicant']]

            # Поле 441 (дата опубликования заявки)
            if res['TradeMark']['TrademarkDetails'].get('Code_441'):
                del res['TradeMark']['TrademarkDetails']['Code_441']
            if not res['TradeMark']['TrademarkDetails'].get('Code_441'):
                try:
                    e_bulletin_app = EBulletinData.objects.get(
                        app_number=res['TradeMark']['TrademarkDetails'].get('ApplicationNumber')
                    )
                except EBulletinData.DoesNotExist:
                    pass
                else:
                    res['TradeMark']['TrademarkDetails']['Code_441'] = e_bulletin_app.publication_date

            # Поисковые данные (для сортировки и т.д.)
            res['search_data'] = {
                'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                'app_number': res['TradeMark']['TrademarkDetails'].get('ApplicationNumber'),
                'protective_doc_number': res['TradeMark']['TrademarkDetails'].get('RegistrationNumber'),
                'rights_date': res['TradeMark']['TrademarkDetails'].get('RegistrationDate'),
                'applicant': applicant,
                'owner': [{'name': x['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine']} for x in
                          res['TradeMark']['TrademarkDetails']['HolderDetails']['Holder']]
                if res['TradeMark']['TrademarkDetails'].get('HolderDetails') else None,
                'title': ', '.join([x['#text'] for x in res['TradeMark']['TrademarkDetails']['WordMarkSpecification'][
                    'MarkSignificantVerbalElement']])
                if res['TradeMark']['TrademarkDetails'].get('WordMarkSpecification') else None,
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

            # fix TradeMark.Transactions.Transaction.TransactionBody.PublicationDetails.Publication.PublicationDate
            if res['TradeMark'].get('Transactions', {}).get('Transaction'):
                for transaction in res['TradeMark']['Transactions']['Transaction']:
                    try:
                        d = transaction['TransactionBody']['PublicationDetails']['Publication'][
                            'PublicationDate']
                        transaction['TransactionBody']['PublicationDetails']['Publication'][
                            'PublicationDate'] = datetime.datetime.strptime(d, '%d.%m.%Y').strftime('%Y-%m-%d')
                    except:
                        pass

            # Fix id_doc_cead
            self.fix_id_doc_cead(res['TradeMark'].get('DocFlow', {}).get('Documents', []))

            # Переименование изображения
            self.rename_image_tm(doc, res)

            # Запись в индекс
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

            # fix priority date
            try:
                if res['Design']['DesignDetails'].get('PriorityDetails', {}).get('Priority'):
                    for item in res['Design']['DesignDetails']['PriorityDetails']['Priority']:
                        if not item['PriorityDate']:
                            del item['PriorityDate']
            except AttributeError:
                pass

            # fix Design.Transactions.Transaction.TransactionBody.PublicationDetails.Publication.PublicationDate
            if res['Design'].get('Transactions', {}).get('Transaction'):
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

            # Поисковые данные (для сортировки и т.д.)
            res['search_data'] = {
                'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                'app_number': res['Geo']['GeoDetails'].get('ApplicationNumber'),
                'app_date': res['Geo']['GeoDetails'].get('ApplicationDate'),
                'protective_doc_number': res['Geo']['GeoDetails'].get('RegistrationNumber'),
                'rights_date': res['Geo']['GeoDetails'].get('RegistrationDate'),
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

            # Статус охранного документа (цвет)
            data['search_data']['registration_status_color'] = get_registration_status_color(data)

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
                cr_data = res['Certificate']['CopyrightDetails']
            else:   # Договоры
                # Секция Decision
                res['Decision'] = data.get('Decision')
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
                'registration_status_color': 'green',
            }

            # Запись в индекс
            self.write_to_es_index(doc, res)

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
                last_indexation_date=timezone.now()
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

    def rename_image_tm(self, doc, data):
        """Переименовывает изображение ТМ."""
        try:
            mark_image = data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']
            app_number = data['TradeMark']['TrademarkDetails']['ApplicationNumber']
        except KeyError:
            pass
        else:
            doc_files_path = self.get_doc_files_path(doc)
            old_file = os.path.join(doc_files_path, mark_image['MarkImageFilename'])

            # Проверка было ли изображение уже переименовано
            if os.path.exists(old_file):  # не переименовано - первоначальный файл найден на диске
                new_file_name = mark_image['MarkImageFilename'].replace(app_number, str(uuid.uuid4()))

                # Переименование файла на диске
                new_file = os.path.join(doc_files_path, new_file_name)
                os.rename(old_file, new_file)

                mark_image['MarkImageFilename'] = new_file_name
            else:
                ext = old_file.split('.')[1]
                for file in os.listdir(doc_files_path):
                    if file.endswith(ext):
                        mark_image['MarkImageFilename'] = file
                        break


    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        self.es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)

        # Получение документов для индексации
        documents = IpcAppList.objects.values(
            'id',
            'files_path',
            'obj_type_id',
            'registration_number',
            'registration_date',
            'app_number',
            'app_date',
            'app_input_date',
        ).exclude(registration_date__gte=timezone.now())
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
                documents = documents.filter(registration_number='')
            elif status == 2:
                documents = documents.exclude(registration_number='')

        # Создание процесса индексации в БД
        self.indexation_process = IndexationProcess.objects.create(
            begin_date=timezone.now(),
            not_indexed_count=documents.count()
        )

        self.stdout.write(self.style.SUCCESS('The list of documents has been successfully received.'))

        for doc in documents:
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
