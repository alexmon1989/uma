"""
Сервисы, которые обращаются к внешним системам и ресурсам.
"""

import pyodbc
from django.db import connections


def cead_get_id_doc(barcode: str) -> str | None:
    """Возвращает idDocCead документа из ЦЭАД"""
    with connections['e_archive'].cursor() as cursor:
        cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
        cursor.execute(
            "SELECT idDoc FROM EArchive WHERE BarCODE=%s",
            [barcode]
        )
        row = cursor.fetchone()
        if row:
            return row[0]
    return None


def application_has_sanctions(id_obj_type: int, app_number: str = None, reg_number: str = None) -> bool:
    """Повертає ознаку того чи знаходиться об'єкт під санкціями."""
    if app_number is None and reg_number is None:
        return False

    # Тип об'єкта у БД GLOC
    gloc_obj_types = {
        1: [300, 301],
        2: [302, 303],
        3: [309, 310],
        4: [304, 305],
        5: [311, 312],
        6: [307, 308],
        9: [306, ],
        14: [306, ],
    }

    try:
        obj_types = gloc_obj_types[id_obj_type]
        obj_number = [app_number]
        if reg_number:
            obj_number.append(reg_number)
        obj_types_placeholder = ', '.join(str(x) for x in obj_types)
        obj_number_placeholder = ', '.join(f"'{x}'" for x in obj_number)
    except KeyError:
        return False
    else:
        with connections['gloc'].cursor() as cursor:
            cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
            query = (
                f"SELECT COUNT(*) "
                f"FROM rr_sanctioned_objects "
                f"WHERE idState=125 AND idObjType IN ({obj_types_placeholder}) "
                f"AND ObjNumber IN ({obj_number_placeholder})"
            )
            cursor.execute(query)
            row = cursor.fetchone()
            return row[0] > 0
