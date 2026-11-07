from celery import shared_task
from .services import OriginalDocumentService


@shared_task
def get_original_document(sec_code):
    """Получает оригинал документа, ЭЦП, сохраняет их на диск в виде архива и возвращает путь к архиву."""
    service = OriginalDocumentService(sec_code)
    return service.create_original_document_archive()
