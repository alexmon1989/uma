"""
Сервисы, которые обращаются к внешним системам и ресурсам.
"""
import datetime

import pyodbc
from typing import List, Tuple, Set
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


class CeadLimitsService:
    """Сервіс для отримання даних щодо обмежень у ЦЕАД."""

    # Відповідність ідентифікаторів типів об'єктів між СІС та ЦЕАД
    obj_types_cead: dict = {
        1: 1,
        2: 8,
        3: 4,
        4: 2,
        5: 5,
        6: 3,
        9: 14,
        10: 10,
        11: 11,
        12: 12,
        13: 13,
    }

    def get_list(self, datetime_from: datetime.datetime, datetime_to: datetime.datetime) -> List[Tuple[str, int]]:
        """Повертає список заявок, до яких були застосовані обмеження за період часу.

        :param datetime_from: Дата та час початку періоду
        :type datetime_from: datetime.datetime
        :param datetime_to: Дата та час закінчення періоду
        :type datetime_to: datetime.datetime

        :return: список номерів заявок з їх типами ОПВ
        :rtype: List[Tuple[str, int]]
        """
        query = 'EXEC [ext].[uma_GetLimitObjects] @dateBegin = %s, @dateEnd = %s'

        res = []

        obj_types_cead_reversed = dict((v, k) for k, v in self.obj_types_cead.items())
        with connections['e_archive'].cursor() as cursor:
            cursor.execute(
                query,
                [datetime_from.strftime('%Y-%m-%d %H:%M:%S'), datetime_to.strftime('%Y-%m-%d %H:%M:%S')]
            )
            while True:
                next_row = cursor.fetchone()
                if next_row:
                    res.append((next_row[0], obj_types_cead_reversed[next_row[1]]))
                else:
                    break

        return res

    def get_limit_details(self, app_number: str, obj_type_id: int) -> Tuple[int | None, Set[int]]:
        """Повертає інформацію з ЦЕАД щодо обмежень опублікованих даних (статус, обмежених список полей).

        :param app_number: Номер заявки
        :type app_number: str
        :param obj_type_id: Ідентифікатор типу об'єкта у СІС
        :type obj_type_id: int

        :return: кортеж, у якому перший елемент - ідентифікатор статусу обмеження або None,
        другий - список полей, що обмежуються.
        :rtype: Tuple[int | None, List[tuple]]

        Значення статусу обмежень:
        922	- встановлено обмеження
        923 - знято обмеження
        924 - відсутні обмеження

        Значення у списку обмежених полей:
        1 - (71) ім’я або повне найменування заявника (заявників)
        2 - (72) ім’я винахідника (винахідників)
        3 - (73) ім’я або повне найменування та адреса володільця(ів) патенту
        4 - (98) адреса та ім’я фізичної або повне найменування юридичної особи, якій надсилається патент, адреса для листування
        5 - Формула
        6 - Опис
        7 - Реферат
        8 - Головне креслення
        9 - (54) Назва винаходу
        10 - (56) Патенти аналоги
        11 - (74) Найменування представника
        40 - (55) зображення промислового зразка
        41 - (71) ім’я або повне найменування та адреса заявника (заявників)
        42 - (72) ім’я автора (авторів) (за наявності)
        43 - (73) ім’я або повне найменування та адреса власника(ів) промислового зразка
        44 - (98) адреса та ім’я фізичної або повне найменування юридичної особи, якій надсилається свідоцтво, адреса для листування
        45 - Назва промислового зразка
        46 - (74) Найменування представника
        12 - Прізвище, ім’я по батькові (за наявності) та/або псевдонім автора (авторів)
        13 - Відомості про оприлюднення твору
        14 - Анотація або реферат твору
        15 - Прізвище, ім’я, по батькові або повне найменування особи (осіб), якій (яким) належать майнові права на твір
        16 - Прізвище, ім’я, по батькові (за наявності) або повне найменування представника
        17 - Назва твору
        18 - Прізвище, ім’я, по батькові або повне найменування осіб – сторін договору
        19 - Способи використання твору, майнові права на які передаються (надаються) за договором
        20 - Територія
        21 - Строк, на який надано права за договором (для ліцензійних договорів)
        22 - Вид і назва договору
        23 - Номер договору і дата його підписання
        35 - Прізвище, ім’я по батькові та/або псевдонім автора (авторів)
        36 - Відомості про оприлюднення твору
        37 - Анотація або реферат твору
        38 - Назва твору
        39 - Прізвище, ім’я, по батькові (за наявності) або повне найменування представника
        """

        # Виклик збереженої процедури з ЦЕАД
        query = f"""
            DECLARE @appNumber VARCHAR(50) = '{app_number}';
            DECLARE @idObjType INT = {self.obj_types_cead[obj_type_id]};
            DECLARE @idStatus INT;
            
            EXEC [ext].[uma_GetLimitsInfoForObject]
                @appNumber = @appNumber,
                @idObjType = @idObjType,
                @idStatus = @idStatus OUTPUT;
    
            SELECT @idStatus AS idStatus;
        """

        with connections['e_archive'].cursor() as cursor:
            cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
            cursor.execute(query)
            muc_list = cursor.fetchall()
            cursor.nextset()
            status = cursor.fetchone()
            if status:
                status = status[0]

            return status, {x[0] for x in muc_list}


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


def madrid_notif_get_ua_bul(date: str) -> tuple[int, int] | None:
    """Повертає номер та рік українськрого бюлетеня, у якому були відображені дані мадридського бюлетеня."""
    cache_key = f"madrid_notif_bulletin_{date}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    with connections['ellav'].cursor() as cursor:
        query = f"""
            SELECT BulletinNumber, BulletinYear
            FROM OPENQUERY(
                [HIPPO,51433],
                'SELECT BulletinNumber, BulletinYear
                 FROM MadridNotif.dbo.GazetteBulletins
                 WHERE IsDeleted = 0 AND GazettePublicationDate = ''{date}''
                 ORDER BY GazettePublicationDate'
            )
        """
        cursor.execute(query)
        res = cursor.fetchone()
        if res:
            result = (res[0], res[1])
            cache.set(cache_key, result, timeout=3600)
            return result

        cache.set(cache_key, None, timeout=3600)
        return None
