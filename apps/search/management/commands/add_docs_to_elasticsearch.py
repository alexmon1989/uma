from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from elasticsearch import Elasticsearch
from apps.search.models import IpcAppList
import os
import json


class Command(BaseCommand):
    help = 'Adds or updates documents in ElasticSearch index.'

    def handle(self, *args, **options):
        # Инициализация клиента ElasticSearch
        es = Elasticsearch()

        # Получение документов для индексации
        documents = IpcAppList.objects.filter(elasticindexed=0)

        for doc in documents:
            # Путь к файлам объекта
            doc_files_path = doc.files_path.replace(
                '\\\\bear\\share\\',
                settings.DOCUMENTS_MOUNT_FOLDER
            ).replace('\\', '/')

            # Формирование результирующего словаря для записи в ElasticSearch:

            # Изобретения, полезные модели
            if doc.obj_type_id in (1, 2):
                res = {}

                # Статус объекта (1 - заявка, 2 - охранный документ)
                status = 2 if doc.registration_number else 1

                # Общие данные объекта
                res['Document'] = {
                    'Status': status,
                    'idObjType': doc.obj_type_id,
                    'filesPath': doc.files_path,
                    'idAPPNumber': doc.id,
                }

                # Путь к файлу JSON с данными объекта:
                file_name = doc.app_number if status == 1 else doc.registration_number
                json_path = os.path.join(doc_files_path, f"{file_name}.json")

                try:
                    f = open(json_path, 'r', encoding='utf16')
                    try:
                        # Чтение содержимого JSON
                        data = json.loads(f.read())

                        # Данные объекта
                        if data.get('Patent'):
                            res['Patent'] = data['Patent']
                        else:
                            res['Patent'] = data['Claim']
                        if data.get('DOCFLOW'):
                            res['DOCFLOW'] = data['DOCFLOW']

                        # Запись в индекс
                        #es.index(index=settings.ELASTIC_INDEX_NAME, doc_type='_doc', id=doc.id, body=res)

                        # Пометка в БД что этот документ проиндексирован
                        #doc.elasticindexed = 1
                        #doc.save()

                    except json.decoder.JSONDecodeError:
                        self.stdout.write(
                            self.style.ERROR(f"Error: can't parse JSON in file: {json_path}"))

                except FileNotFoundError:
                    self.stdout.write(self.style.ERROR(f"File not found: {json_path}"))

        self.stdout.write(self.style.SUCCESS('Finished'))
