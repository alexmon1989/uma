from .models import DocumentTypeNacp

from typing import List


def document_types_disabled_nacp(titles: List[str], obj_type_id: int) -> List[str]:
    """Возвращает типы документов, которые не доступны для скачивания."""
    enabled = DocumentTypeNacp.objects.filter(
        title__in=titles,
        enabled=True,
        obj_types__id=obj_type_id
    ).values_list('title', flat=True)

    # Возвращается разница между двумя списками, т.е. то что не разрешено для скачивания
    return [x for x in titles if x not in enabled]
