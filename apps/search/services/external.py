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
