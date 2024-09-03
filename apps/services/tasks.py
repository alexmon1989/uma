from django.db import connections
from django.conf import settings
from celery import shared_task
from zipfile import ZipFile
import os


@shared_task
def get_original_document(sec_code):
    """Получает оригинал документа, ЭЦП, сохраняет их на диск в виде архива и возвращает путь к архиву."""
    with connections['e_archive'].cursor() as cursor:
        cursor.execute("EXEC ext.uma_getOriginalDocument %s", [sec_code])

        rows = cursor.fetchall()
        if not rows:
            return ''

        file_path = os.path.join(
            settings.MEDIA_ROOT,
            'original_documents',
            f"{sec_code}.zip"
        )

        while rows:
            with ZipFile(file_path, 'w') as zip_:
                for row in rows:
                    if row[2]:
                        zip_.writestr(row[1], row[2])
            if cursor.nextset():
                rows = cursor.fetchall()
            else:
                rows = None

        return os.path.join(
            settings.MEDIA_URL,
            'original_documents',
            f"{sec_code}.zip"
        )
