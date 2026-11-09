import logging
from celery import shared_task
from .services import CertsUpdateService

logger = logging.getLogger(__name__)


@shared_task(name="apps.my_auth.tasks.update_certs_task")
def update_certs_task(backup: bool = True):
    """
    Періодична задача для автоматичного оновлення CAs.json та CACertificates.p7b.
    Запускається через django-celery-beat або celery beat scheduler.
    """
    logger.info("Starting scheduled certificates update task...")
    service = CertsUpdateService()
    result = service.update_certs(backup=backup)
    if result["success"]:
        logger.info(
            "Certificates successfully updated from source: %s",
            result.get("source_used"),
        )
    else:
        logger.error(
            "Certificates update failed. Errors: %s",
            "; ".join(result.get("errors", [])),
        )
    return result

