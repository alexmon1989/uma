from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Max
from elasticsearch import Elasticsearch, exceptions as elasticsearch_exceptions
from elasticsearch_dsl import Search, Q
from apps.search.models import IpcAppList, IndexationError, IndexationProcess
from ...utils import get_registration_status_color
import json
import os.path
import datetime


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

    def process_inv_um_ld(self, doc):
        """Добавляет документ одного из типов (изобретение, полезная модель, топография ИМС) в ElasticSearch."""
        # Получает данные для загрузки из файла JSON
        data = self.get_data_from_json(doc)

        res = {}
        # Проверка не выдан ли патент по заявке
        if data is not None and not (data.get('Document').get('Status') == 3 and data.get('Claim', {}).get('I_11')):
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
                    'applicant': [list(x.values())[0] for x in biblio_data.get('I_71', [])],
                    'inventor': [list(x.values())[0] for x in biblio_data.get('I_72', [])],
                    'owner': [list(x.values())[0] if list(x.keys())[0] != 'EDRPOU'
                              else list(x.values())[1] for x in biblio_data.get('I_73', [])],
                    'agent': biblio_data.get('I_74'),
                    'title': [list(x.values())[0] for x in biblio_data.get('I_54', [])]
                }

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

            # Секция TradeMark
            res['TradeMark'] = data.get('TradeMark')

            # Случай если секции PaymentDetails, DocFlow, Transactions не попали в секцию TradeMark
            if data.get('PaymentDetails'):
                res['TradeMark']['PaymentDetails'] = data.get('PaymentDetails')
            if data.get('DocFlow'):
                res['TradeMark']['DocFlow'] = data.get('DocFlow')
            if data.get('Transactions'):
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
                'app_date': res['TradeMark']['TrademarkDetails'].get('ApplicationDate', doc['app_date']),
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

            # Статус охранного документа (цвет)
            if res['search_data']['obj_state'] == 2:
                res['search_data']['registration_status_color'] = get_registration_status_color(res)

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

            # Секция Design
            res['Design'] = data.get('Design')

            # Случай если секции PaymentDetails, DocFlow, Transactions не попали в секцию Design
            if data.get('PaymentDetails'):
                res['Design']['PaymentDetails'] = data.get('PaymentDetails')
            if data.get('DocFlow'):
                res['Design']['DocFlow'] = data.get('DocFlow')
            if data.get('Transactions'):
                res['Design']['Transactions'] = data.get('Transactions')

            applicant = None
            if res['Design']['DesignDetails'].get('ApplicantDetails'):
                applicant = [x['ApplicantAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                                 'FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                             res['Design']['DesignDetails']['ApplicantDetails']['Applicant']]

            # Поисковые данные (для сортировки и т.д.)
            res['search_data'] = {
                'obj_state': 2 if (doc['registration_number'] and doc['registration_number'] != '0') else 1,
                'app_number': res['Design']['DesignDetails'].get('DesignApplicationNumber'),
                'app_date': res['Design']['DesignDetails'].get('DesignApplicationDate', doc['app_date']),
                'protective_doc_number': res['Design']['DesignDetails'].get('RegistrationNumber'),
                'rights_date': res['Design']['DesignDetails'].get('RecordEffectiveDate'),
                'applicant': applicant,

                'inventor': [x['DesignerAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                          res['Design']['DesignDetails']['DesignerDetails']['Designer']]
                if res['Design']['DesignDetails'].get('DesignerDetails') else None,

                'owner': [x['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                          res['Design']['DesignDetails']['HolderDetails']['Holder']]
                if res['Design']['DesignDetails'].get('HolderDetails') else None,

                'agent': [x['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                          res['Design']['DesignDetails']['RepresentativeDetails']['Representative']
                          if x.get('RepresentativeAddressBook')]
                if res['Design']['DesignDetails'].get('RepresentativeDetails') else None,

                'title': res['Design']['DesignDetails'].get('DesignTitle')
            }

            # Статус охранного документа (цвет)
            if res['search_data']['obj_state'] == 2:
                res['search_data']['registration_status_color'] = get_registration_status_color(res)

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
                'owner': [x['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                          res['Geo']['GeoDetails']['HolderDetails']['Holder']]
                if res['Geo']['GeoDetails'].get('HolderDetails') else None,

                'agent': [x['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                              'FreeFormatNameDetails']['FreeFormatNameLine'] for x in
                          res['Geo']['GeoDetails']['RepresentativeDetails']['Representative']]
                if res['Geo']['GeoDetails'].get('RepresentativeDetails') else None,

                'title': res['Geo']['GeoDetails'].get('Indication'),
            }

            # Статус охранного документа (цвет)
            if res['search_data']['obj_state'] == 2:
                res['search_data']['registration_status_color'] = get_registration_status_color(res)

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
            # Пометка в БД что этот документ проиндексирован
            IpcAppList.objects.filter(id=doc['id']).update(elasticindexed=1)

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
        documents = IpcAppList.objects.filter(elasticindexed=0).values(
            'id',
            'files_path',
            'obj_type_id',
            'registration_number',
            'app_number',
            'app_date',
        )
        # Фильтрация по параметрам командной строки
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
            begin_date=datetime.datetime.now(),
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
            # Увеличение счётчика обработанных документов
            self.indexation_process.processed_count += 1
            self.indexation_process.save()

            # Удаление JSON
            try:
                os.remove(self.get_json_path(doc))
            except FileNotFoundError:
                pass

        # Время окончания процесса индексации и сохранение данных процесса индексации
        self.indexation_process.finish_date = datetime.datetime.now()

        qs = Q('query_string', query='*')
        # Количество документов в индексе
        s = Search(using=self.es, index=settings.ELASTIC_INDEX_NAME).query(qs)
        self.indexation_process.documents_in_index = s.count()
        self.indexation_process.save()

        # Заполнение поля NotificationDate в таблице IPC_AppList
        self.fill_notification_date()

        self.stdout.write(self.style.SUCCESS('Finished'))
