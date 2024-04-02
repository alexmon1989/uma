from django.core.management.base import BaseCommand
from django.conf import settings

from apps.search.models import IpcAppList

import datetime
import pathlib
import shutil
import os
import ftplib


class Command(BaseCommand):
    help = 'Creates and uploads archive with inv and um materials to EPO'

    def add_arguments(self, parser):
        parser.add_argument(
            '--registration_date',
            type=str,
            default=datetime.datetime.now().strftime('%d.%m.%Y'),
            help='Registration date / bulletin date in format dd.mm.yyyy'
        )
        parser.add_argument(
            '--verbose',
            type=bool,
            help='Show progress'
        )

    def _create_and_fill_folder(self, registration_date: str) -> pathlib.Path:
        new_patents = IpcAppList.objects.filter(
            obj_type__id__in=(1, 2)
        ).prefetch_related('appdocuments_set')

        updated_patents = IpcAppList.objects.filter(
            obj_type__id__in=(1, 2)
        ).exclude(registration_date__isnull=True, is_limited=True).prefetch_related('appdocuments_set')

        registration_date_from = datetime.datetime.strptime(
            f"{registration_date} 00:00:00",
            '%d.%m.%Y %H:%M:%S'
        )
        registration_date_to = datetime.datetime.strptime(
            f"{registration_date} 23:59:59",
            '%d.%m.%Y %H:%M:%S'
        )
        new_patents = new_patents.filter(
            registration_date__gte=registration_date_from, registration_date__lte=registration_date_to
        ).exclude(is_limited=True)

        notification_date = datetime.datetime.strptime(registration_date, '%d.%m.%Y')
        updated_patents = updated_patents.filter(notification_date=notification_date)

        # Путь к каталогу, в который будет складываться информация
        folder_path = pathlib.Path(
            settings.DOCUMENTS_MOUNT_FOLDER
        ) / 'EPO_upload' / f"UA_{registration_date.replace('.', '_')}"
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
            except OSError:
                pass

        # Копирование файлов новых патентов
        for patent in new_patents:
            for doc in patent.appdocuments_set.all():
                file_path_full = pathlib.Path(doc.file_name.replace(
                    '\\\\bear\\share\\', settings.DOCUMENTS_MOUNT_FOLDER
                ).replace(
                    '\\', '/'
                ))
                dest = folder_path / 'New' / patent.registration_number / file_path_full.name
                os.makedirs(dest.parent, exist_ok=True)
                shutil.copy(file_path_full, dest)

        # Копирование файлов изменённых патентов
        for patent in updated_patents:
            for doc in patent.appdocuments_set.all():
                file_path_full = pathlib.Path(doc.file_name.replace(
                    '\\\\bear\\share\\', settings.DOCUMENTS_MOUNT_FOLDER
                ).replace(
                    '\\', '/'
                ))
                dest = folder_path / 'Updated' / patent.registration_number / file_path_full.name
                os.makedirs(dest.parent, exist_ok=True)
                shutil.copy(file_path_full, dest)

        return folder_path

    def handle(self, *args, **options):
        # Формирование каталога
        if options['verbose']:
            print('Folder filling')
        folder_path = self._create_and_fill_folder(options['registration_date'])

        # Архивирование каталога
        if options['verbose']:
            print('Folder archiving')
        if os.path.exists(folder_path):
            shutil.make_archive(str(folder_path), 'zip', folder_path)

            # Загрузка на ФТП
            if options['verbose']:
                print('FTP uploading')
            HOSTNAME = settings.EPO_FTP_HOSTNAME
            USERNAME = settings.EPO_FTP_USERNAME
            PASSWORD = settings.EPO_FTP_PASSWORD
            ftp_server = ftplib.FTP(HOSTNAME, USERNAME, PASSWORD)
            ftp_server.encoding = "utf-8"

            zip_path_local = f"{str(folder_path)}.zip"
            zip_path_ftp = f"{settings.EPO_FTP_DIRECTORY}/{folder_path.name}.zip"
            with open(zip_path_local, "rb") as file:
                ftp_server.storbinary(f"STOR {zip_path_ftp}", file)

            # Удаление
            if options['verbose']:
                print('Folder removing')
            try:
                shutil.rmtree(folder_path)
            except OSError:
                if options['verbose']:
                    print(f'Warning: could not remove folder {folder_path}')
