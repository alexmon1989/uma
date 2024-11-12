"""
Сервисы, которые обращаются к внешним системам и ресурсам.
"""

import pyodbc
from typing import List
from django.db import connections
from django.core.cache import cache


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


def gloc_get_sanctioned_objects() -> List[dict]:
    """Отримує санкційні об'єкти з БД GLOC, кешує результат на 1 год."""
    cache_key = "rr_sanctioned_objects"
    rr_sanctioned_objects = cache.get(cache_key)
    if rr_sanctioned_objects:
        return rr_sanctioned_objects

    rr_sanctioned_objects = []
    with connections['gloc'].cursor() as cursor:
        cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
        query = "SELECT DISTINCT ObjNumber, idObjType " \
                "FROM rr_sanctioned_objects " \
                "WHERE idState = 125 ORDER BY idObjType"
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            obj_number, obj_type = row
            rr_sanctioned_objects.append(
                {
                    'obj_number': obj_number,
                    'id_obj_type': obj_type
                }
            )
        cache.set(cache_key, rr_sanctioned_objects, 3600)
        return rr_sanctioned_objects
