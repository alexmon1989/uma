from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch, exceptions as elasticsearch_exceptions
from apps.search.models import IpcAppList, IndexationError
import json
import os.path
import datetime


class Command(BaseCommand):
    help = 'Adds or updates documents in ElasticSearch index.'
    es = None

    def get_json_path(self, doc):
        """Получает путь к файлу JSON с данными объекта."""
        # Путь к файлам объекта
        doc_files_path = doc['files_path'].replace(
            '\\\\bear\\share\\',
            settings.DOCUMENTS_MOUNT_FOLDER
        ).replace('\\', '/')

        # Путь к файлу JSON с данными объекта:
        file_name = doc['registration_number'] \
            if (doc['registration_number'] and doc['registration_number'] != '0') \
            else doc['app_number']
        file_name = file_name.replace('/', '_')

        json_path = os.path.join(doc_files_path, f"{file_name}.json")
        if not os.path.exists(json_path):
            json_path = os.path.join(doc_files_path, f"{file_name}-К.json")

        return json_path

    def get_data_from_json(self, doc):
        """Получает словарь с данными из файла JSON."""
        json_path = self.get_json_path(doc)

        data = None

        # Чтение содержимого JSON в data
        try:
            f = open(json_path, 'r', encoding='utf16')
            try:
                data = json.loads(f.read())
            except json.decoder.JSONDecodeError as e:
                self.stdout.write(self.style.ERROR(f"JSONDecodeError: {e}: {json_path}"))
                IndexationError.objects.create(
                    app_id=doc['id'],
                    type='JSONDecodeError',
                    text=e,
                    json_path=json_path
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
                    json_path=json_path
                )
        except FileNotFoundError as e:
            self.stdout.write(self.style.ERROR(f"FileNotFoundError: {e}"))
            IndexationError.objects.create(
                app_id=doc['id'],
                type='FileNotFoundError',
                text=e,
                json_path=json_path
            )

        return data

    def process_inv_um_ld(self, doc):
        """Добавляет документ одного из типов (изобретение, полезная модель, топография ИМС) в ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)

        res = {}
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
                    json_path=json_path
                )
            else:
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

                # Поисковые данные (для сортировки и т.д.)
                res['search_data'] = {
                    'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                    'app_number': biblio_data.get('I_21'),
                    'app_date': biblio_data.get('I_22'),
                    'protective_doc_number': biblio_data.get('I_11'),
                    'rights_date': biblio_data.get('I_24'),
                    'applicant': [list(x.values())[0] for x in biblio_data.get('I_71', [])],
                    'inventor': [list(x.values())[0] for x in biblio_data.get('I_72', [])],
                    'owner': [list(x.values())[0] for x in biblio_data.get('I_73', [])],
                    'agent': biblio_data.get('I_74'),
                    'title': [list(x.values())[0] for x in biblio_data.get('I_54', [])],
                }

                # Запись в индекс
                try:
                    self.es.index(index=settings.ELASTIC_INDEX_NAME, doc_type='_doc', id=doc['id'], body=res)
                except elasticsearch_exceptions.RequestError as e:
                    json_path = self.get_json_path(doc)
                    self.stdout.write(self.style.ERROR(f"ElasticSearch RequestError: {e}: {json_path}"))
                    IndexationError.objects.create(
                        app_id=doc['id'],
                        type='ElasticSearch RequestError',
                        text=e,
                        json_path=json_path
                    )
                else:
                    # Пометка в БД что этот документ проиндексирован
                    IpcAppList.objects.filter(id=doc['id']).update(elasticindexed=1)

    def process_tm(self, doc):
        """Добавляет документ типа "знак для товаров и услуг" ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)

        res = {}
        if data is not None:
            # Секция Document
            res['Document'] = data.get('Document')

            # Секция TradeMark
            res['TradeMark'] = data.get('TradeMark')

            # Случай если секции PaymentDetails, DocFlow, Transactions не попали в секцию TradeMark
            if data.get('PaymentDetails'):
                res['TradeMark']['PaymentDetails'] = data.get('PaymentDetails')
            if data.get('DocFlow'):
                res['TradeMark']['DocFlow'] = data.get('DocFlow')
            if data.get('PaymentDetails'):
                res['TradeMark']['Transactions'] = data.get('Transactions')

            # Форматирование даты
            if res['TradeMark'].get('PublicationDetails', {}).get('PublicationDate'):
                try:
                    d = datetime.datetime.today().strptime(
                        res['TradeMark']['PublicationDetails']['PublicationDate'],
                        '%d.%m.%Y'
                    )
                except ValueError:
                    pass
                else:
                    res['TradeMark']['PublicationDetails']['PublicationDate'] = d.strftime('%Y-%m-%d')

            applicant = None
            if res['TradeMark']['TrademarkDetails'].get('ApplicantDetails'):
                applicant = [x['ApplicantAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                                 'FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                             res['TradeMark']['TrademarkDetails']['ApplicantDetails']['Applicant']]

            # Поисковые данные (для сортировки и т.д.)
            res['search_data'] = {
                'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                'app_number': res['TradeMark']['TrademarkDetails'].get('ApplicationNumber'),
                'app_date': res['TradeMark']['TrademarkDetails'].get('ApplicationDate'),
                'protective_doc_number': res['TradeMark']['TrademarkDetails'].get('RegistrationNumber'),
                'rights_date': res['TradeMark']['TrademarkDetails'].get('RegistrationDate'),
                'applicant': applicant,
                'owner': [x['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                          res['TradeMark']['TrademarkDetails']['HolderDetails']['Holder']]
                if res['TradeMark']['TrademarkDetails'].get('HolderDetails') else None,

                'agent': [x['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                          res['TradeMark']['TrademarkDetails']['RepresentativeDetails']['Representative']]
                if res['TradeMark']['TrademarkDetails'].get('RepresentativeDetails') else None,

                'title': ', '.join([x['#text'] for x in res['TradeMark']['TrademarkDetails']['WordMarkSpecification'][
                    'MarkSignificantVerbalElement']])
                if res['TradeMark']['TrademarkDetails'].get('WordMarkSpecification') else None,
            }

            # Запись в индекс
            try:
                self.es.index(index=settings.ELASTIC_INDEX_NAME, doc_type='_doc', id=doc['id'], body=res)
            except elasticsearch_exceptions.RequestError as e:
                json_path = self.get_json_path(doc)
                self.stdout.write(self.style.ERROR(f"ElasticSearch RequestError: {e}: {json_path}"))
                IndexationError.objects.create(
                    app_id=doc['id'],
                    type='ElasticSearch RequestError',
                    text=e,
                    json_path=json_path
                )
            else:
                # Пометка в БД что этот документ проиндексирован
                IpcAppList.objects.filter(id=doc['id']).update(elasticindexed=1)

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        self.es = Elasticsearch()

        # Получение документов для индексации
        documents = IpcAppList.objects.filter(elasticindexed=0).values(
            'id',
            'files_path',
            'obj_type_id',
            'registration_number',
            'app_number'
        ).all()
        self.stdout.write(self.style.SUCCESS('The list of documents has been successfully received.'))

        for doc in documents:
            # Изобретения, полезные модели, топографии интегральных микросхем
            if doc['obj_type_id'] in (1, 2, 3):
                self.process_inv_um_ld(doc)
            # Знаки для товаров и услуг
            elif doc['obj_type_id'] == 4:
                self.process_tm(doc)

        self.stdout.write(self.style.SUCCESS('Finished'))
