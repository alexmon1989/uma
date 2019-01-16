from django.core.management.base import BaseCommand
from django.conf import settings
from elasticsearch import Elasticsearch, exceptions as elasticsearch_exceptions
from apps.search.models import IpcAppList
import json
import apps.search.chardet_open as chardet_open
import os.path


class Command(BaseCommand):
    help = 'Adds or updates documents in ElasticSearch index.'

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch()

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
            # Путь к файлам объекта
            doc_files_path = doc['files_path'].replace(
                '\\\\bear\\share\\',
                settings.DOCUMENTS_MOUNT_FOLDER
            ).replace('\\', '/')

            """ Формирование результирующего словаря для записи в ElasticSearch: """
            # Изобретения, полезные модели, топографии интегральных микросхем
            if doc['obj_type_id'] in (1, 2, 3):
                # Путь к файлу JSON с данными объекта:
                file_name = doc['registration_number'] if doc['registration_number'] else doc['app_number']
                json_path = os.path.join(doc_files_path, f"{file_name}.json")
                if not os.path.exists(json_path):
                    json_path = os.path.join(doc_files_path, f"{file_name}-К.json")

                res = {}
                try:
                    f = chardet_open.open(json_path, 'r')
                    try:
                        # Чтение содержимого JSON
                        data = json.loads(f.read())

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
                            self.stdout.write(
                                self.style.ERROR(f"Error: biblio data missed in file: {json_path}"))
                        else:
                            # Обработка I_72 для избежания ошибки добавления в индекс ElasticSearch
                            for I_72 in biblio_data.get('I_72', []):
                                if I_72.get('I_72.N'):
                                    I_72['I_72.N.E'] = I_72.pop('I_72.N')
                                if I_72.get('I_72.C'):
                                    I_72['I_72.C.E'] = I_72.pop('I_72.C')

                            # Обработка I_73 для избежания ошибки добавления в индекс ElasticSearch
                            for I_72 in biblio_data.get('I_73', []):
                                if I_72.get('I_73.N.U'):
                                    I_72['I_73.N'] = I_72.pop('I_73.N.U')
                                if I_72.get('I_73.N.R'):
                                    I_72['I_73.N'] = I_72.pop('I_73.N.R')
                                if I_72.get('I_73.N.E'):
                                    I_72['I_73.N'] = I_72.pop('I_73.N.E')
                                if I_72.get('I_73.C.U'):
                                    I_72['I_73.C'] = I_72.pop('I_73.C.U')
                                if I_72.get('I_73.C.R'):
                                    I_72['I_73.C'] = I_72.pop('I_73.C.R')
                                if I_72.get('I_73.C.E'):
                                    I_72['I_73.C'] = I_72.pop('I_73.C.E')

                            # Состояние делопроизводства
                            if data.get('DOCFLOW'):
                                res['DOCFLOW'] = data['DOCFLOW']

                            # Оповещения
                            if data.get('TRANSACTIONS'):
                                res['TRANSACTIONS'] = data['TRANSACTIONS']

                            # Поисковые данные (для сортировки и т.д.)
                            res['search_data'] = {
                                'obj_state': 2 if doc['registration_number'] else 1,
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
                                es.index(index=settings.ELASTIC_INDEX_NAME, doc_type='_doc', id=doc['id'], body=res)
                            except elasticsearch_exceptions.RequestError as e:
                                self.stdout.write(self.style.ERROR(f"ElasticSearch RequestError: {e}: {json_path}"))
                            else:
                                # Пометка в БД что этот документ проиндексирован
                                IpcAppList.objects.filter(id=doc['id']).update(elasticindexed=1)

                    except json.decoder.JSONDecodeError as e:
                        self.stdout.write(self.style.ERROR(f"JSONDecodeError: {e}: {json_path}"))

                except FileNotFoundError as e:
                    self.stdout.write(self.style.ERROR(f"FileNotFoundError: {e}"))
                except UnicodeDecodeError as e:
                    self.stdout.write(self.style.ERROR(f"UnicodeDecodeError: {e}: {json_path}"))
                except UnicodeError as e:
                    self.stdout.write(self.style.ERROR(f"UnicodeError: {e}: {json_path}"))

        self.stdout.write(self.style.SUCCESS('Finished'))
