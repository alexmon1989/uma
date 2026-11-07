import os
import uuid
from zipfile import ZipFile
from django.conf import settings
from django.db import connections


class OriginalDocumentService:
    """Сервис для получения и формирования оригиналов документов из Е-Архива."""

    def __init__(self, sec_code: str):
        self.sec_code = sec_code

    def create_original_document_archive(self) -> str:
        """Получает оригинал документа, ЭЦП, сохраняет их на диск в виде архива и возвращает путь к архиву."""
        with connections['e_archive'].cursor() as cursor:
            cursor.execute("EXEC ext.uma_getOriginalDocument %s", [self.sec_code])

            rows = cursor.fetchall()
            if not rows:
                return ''

            filename = f"{uuid.uuid4()}.zip"
            dir_path = os.path.join(
                settings.MEDIA_ROOT,
                'original_documents'
            )
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, filename)

            with ZipFile(file_path, 'w') as zip_:
                while rows:
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
                filename
            )

