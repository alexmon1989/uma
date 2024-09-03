from celery import shared_task
from .models import WKMMark
from .services import WKMImportService


@shared_task
def import_wkm(mark_id: int) -> None:
    """
    Задача Celery для імпорту Добре відомої ТМ у СІС.

    :param int mark_id: ідентифікатор добре відомої ТМ.
    """
    wkm = WKMMark.objects.filter(id=mark_id).using('WellKnownMarks').first()
    import_service = WKMImportService(wkm=wkm)
    import_service.execute()
