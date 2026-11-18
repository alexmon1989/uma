from celery import shared_task
from .services import OriginalDocumentService, original_document_download_log_create


@shared_task
def get_original_document(
    sec_code: str,
    user_id: int | None = None,
    ip: str | None = None,
    user_agent: str = '',
) -> str:
    """Получает оригинал документа, ЭЦП, сохраняет их на диск в виде архива и возвращает путь к архиву."""
    service = OriginalDocumentService(sec_code)
    archive_path = service.create_original_document_archive()
    if archive_path:
        original_document_download_log_create(
            sec_code=sec_code,
            user_id=user_id,
            ip_address=ip,
            user_agent=user_agent,
            file_path=archive_path,
        )
    return archive_path
