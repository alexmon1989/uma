"""
Сервисы, которые обращаются к внешним системам и ресурсам.
"""
import datetime
import io
import subprocess
import tempfile
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple, Set, Type, Any

import pyodbc
from pypdf import PdfReader

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
        47 - (731) Ім'я та адреса заявника
        48 - (732) Ім'я та адреса власника
        49 - (740) Ім'я та адреса представника
        50 - (750) Адреса для листування
        51 - (540) Зображення знака
        52 - (511) Індекси Ніццької класифікації
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


def gloc_get_sanctioned_objects() -> dict[str, list[dict]]:
    """Отримує санкційні об'єкти з БД GLOC, кешує результат на 1 год."""
    cache_key = "rr_sanctioned_objects"
    rr_sanctioned_objects = cache.get(cache_key)
    if rr_sanctioned_objects:
        return rr_sanctioned_objects

    rr_sanctioned_objects = defaultdict(list)
    with connections['gloc'].cursor() as cursor:
        cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
        query = f"""
            SELECT DISTINCT
                s_o.ObjNumber,
                s_o.idObjType,
                s_o.EntityRole,
                s.Source,
                s.TermStart
            FROM
                rr_sanctioned_objects AS s_o
                INNER JOIN rr_sanctioned AS s
                        ON s_o.idSanctioned = s.Id
            WHERE
                idState = 125 AND s.TermEnd >= '{datetime.datetime.now().strftime('%Y-%m-%d')}'
        """
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            obj_number, obj_type, entity_role, source, term_start = row
            rr_sanctioned_objects[obj_number].append(
                {
                    'obj_number': obj_number,
                    'id_obj_type': obj_type,
                    'entity_role': entity_role,
                    'source': source,
                    'term_start': term_start,
                }
            )

    cache.set(cache_key, rr_sanctioned_objects, 3600)
    return rr_sanctioned_objects


class SanctionedObjectsService:
    """Отримує дані щодо санкційних об'єктів права інтелектуальної власності."""

    CACHE_KEY = 'rr_sanctioned_objects'
    CACHE_TTL = 3600

    def __init__(self):
        self._gloc_sanctioned_objects: list[dict] = []
        self._vp3_sanctioned_objects: dict[str, list[dict]] = defaultdict(list)
        self.rr_sanctioned_objects: dict[str, list[dict]] = defaultdict(list)

    def _gloc_get_sanctioned_objects(self) -> None:
        """Отримує дані щодо санкцій з БД GLOC (усі типи об'єктів)."""
        result = []
        with connections['gloc'].cursor() as cursor:
            cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
            query = f"""
                    SELECT DISTINCT
                        s_o.ObjNumber,
                        s_o.idObjType,
                        s_o.EntityRole,
                        s.Source,
                        s.TermStart
                    FROM
                        rr_sanctioned_objects AS s_o
                        INNER JOIN rr_sanctioned AS s
                                ON s_o.idSanctioned = s.Id
                    WHERE
                        idState = 125 AND s.TermEnd >= '{datetime.datetime.now().strftime('%Y-%m-%d')}'
                """
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                obj_number, obj_type, entity_role, source, term_start = row
                result.append(
                    {
                        'obj_number': obj_number,
                        'id_obj_type': obj_type,
                        'entity_role': entity_role,
                        'source': source,
                        'term_start': term_start,
                    }
                )
        self._gloc_sanctioned_objects = result

    def _vp3_get_sanctioned_objects(self) -> None:
        """Отримує дані щодо санкцій з БД VP3 (винаходи, корисні моделі, топографії)."""
        result = defaultdict(list)
        with connections['vp3'].cursor() as cursor:
            cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
            query = f"""
                SELECT 
                    l.name,
                    s.ObjNum,
                    CASE 
                        WHEN s.ObjType = 'Заявка' THEN c.propertyType
                        WHEN s.ObjType = 'Патент' THEN p.propertyType
                        ELSE NULL
                    END AS propertyType
                FROM rr_sanctioned_objects AS s
                LEFT JOIN rr_exp_claim AS c
                    ON c.id = s.ObjIdO
                LEFT JOIN rr_patent AS p
                    ON p.id = s.ObjIdO
                INNER JOIN cl_links AS l
                    ON l.id = s.IdEntityLink
                WHERE s.idState = 912 
                    AND s.ObjType IN ('Патент', 'Заявка') 
                    AND s.sancTermEnd >= '{datetime.datetime.now().strftime('%Y-%m-%d')}'
            """
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                entity_role, obj_number, property_type = row
                result[obj_number].append(
                    {
                        'obj_number': obj_number,
                        'entity_role': entity_role,
                        'property_type': property_type
                    }
                )
        self._vp3_sanctioned_objects = result

    def _merge_sanctioned_objects(self) -> None:
        """Заповнює список санкційних об'єктів даними, отриманими з двох БД"""
        self.rr_sanctioned_objects = defaultdict(list)

        for gloc_item in self._gloc_sanctioned_objects:

            item = gloc_item.copy()

            for vp3_item in self._vp3_sanctioned_objects.get(gloc_item['obj_number'], []):
                obj_type = gloc_item['id_obj_type']

                if obj_type in (300, 301) and vp3_item['property_type'] == 'В':
                    item['entity_role'] = 'власник' if vp3_item['entity_role'] == 'володілець' else vp3_item[
                        'entity_role']

                elif obj_type in (302, 303) and vp3_item['property_type'] == 'К':
                    item['entity_role'] = 'власник' if vp3_item['entity_role'] == 'володілець' else vp3_item[
                        'entity_role']

            self.rr_sanctioned_objects[gloc_item['obj_number']].append(item)

    def _exclude_sanctions(self):
        """Видалення із результуючого списку "зайвих" санкцій."""
        # (obj_number, id_obj_type, entity_role)
        exclusions_set = {
            ('233851', 305, 'Ім’я або повне найменування та адреса власника (власників) свідоцтва'),
            ('227077', 305, 'Ім’я або повне найменування та адреса власника (власників) свідоцтва'),
            ('233852', 305, 'Ім’я або повне найменування та адреса власника (власників) свідоцтва'),
            ('243588', 305, 'Ім’я або повне найменування та адреса власника (власників) свідоцтва'),
            ('238651', 305, 'Ім’я або повне найменування та адреса власника (власників) свідоцтва'),
        }
        for obj_num in list(self.rr_sanctioned_objects.keys()):
            self.rr_sanctioned_objects[obj_num] = [
                obj for obj in self.rr_sanctioned_objects[obj_num]
                if (obj['obj_number'], obj['id_obj_type'], obj['entity_role']) not in exclusions_set
            ]
            if not self.rr_sanctioned_objects[obj_num]:
                del self.rr_sanctioned_objects[obj_num]

    def _append_sanctions(self):
        """Додання санкцій у результуючий список."""
        self.rr_sanctioned_objects['34558'].append(
            {
                'obj_number': '34558',
                'id_obj_type': 308,
                'entity_role': 'Власник(и)',
                'source': 'Указ 191/2023. Додаток 1',
                'term_start': '2023-04-01',
            }
        )
        self.rr_sanctioned_objects['37879'].append(
            {
                'obj_number': '37879',
                'id_obj_type': 308,
                'entity_role': 'Власник(и)',
                'source': 'Указ 191/2023. Додаток 1',
                'term_start': '2023-04-01',
            }
        )

    def get_objects(self) -> dict:
        rr_sanctioned_objects = cache.get(self.CACHE_KEY)
        if rr_sanctioned_objects:
            return rr_sanctioned_objects

        self._gloc_get_sanctioned_objects()
        self._vp3_get_sanctioned_objects()
        self._merge_sanctioned_objects()
        self._exclude_sanctions()
        self._append_sanctions()

        cache.set(self.CACHE_KEY, self.rr_sanctioned_objects, self.CACHE_TTL)

        return self.rr_sanctioned_objects


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


def poznachennya_claim_get_termination_date(app_number: str, obj_type_id: int) -> str | None:
    """Отримує з АС Позначення дата припинення дії(діловодства) заявки."""
    obj_type_mapping = {
        4: 'TORGOVI_MARKY',
        6: 'PROM_ZNAK',
    }
    with connections['prod_erp_cms_claim'].cursor() as cursor:
        query = 'SELECT fn_get_claim_termination_date(%s, %s);'
        cursor.execute(query, [app_number, obj_type_mapping[obj_type_id]])
        res = cursor.fetchone()
        if res:
            return res[0]


def gnof_get_tracking_numbers(doc_numbers: list[str]) -> dict:
    """Повертає словник із трек-номерами документів."""
    with connections['ellav'].cursor() as cursor:
        escaped_doc_numbers = [s.replace("'", "''") for s in doc_numbers]
        doc_numbers_str = ", ".join(f"''{s}''" for s in escaped_doc_numbers)
        query = f"""
            SELECT doc_number, track_number
            FROM OPENQUERY(
                [FOX,51433],
                'WITH MainTS AS (
                    SELECT idMainDocTS
                    FROM GNOF.dbo.rr_documents WITH (NOLOCK)
                    WHERE regNum IN ({doc_numbers_str})
                ),
                Docs AS (
                    SELECT rd.id, rd.regNum, rd.idMainDocTS
                    FROM GNOF.dbo.rr_documents rd WITH (NOLOCK)
                    WHERE rd.idMainDocTS IN (SELECT idMainDocTS FROM MainTS)
                ),
                Barcodes AS (
                    SELECT DISTINCT re.barCode, rd.idMainDocTS
                    FROM GNOF.dbo.rr_documents rd WITH (NOLOCK)
                    INNER JOIN GNOF.dbo.link_objects_num lo WITH (NOLOCK)
                        ON lo.idObject2 = rd.id
                        AND lo.idreestr2 = 205
                        AND lo.idreestr1 = 229
                        AND lo.idlink = 105
                    INNER JOIN GNOF.dbo.rr_envelopes re WITH (NOLOCK)
                        ON re.id = lo.idObject1
                    WHERE re.idType <> 234
                      AND re.sendDate IS NOT NULL
                      AND re.barCode IS NOT NULL
                )
                SELECT d.regNum AS [doc_number], b.barCode AS [track_number]
                    FROM Docs d
                    LEFT JOIN Barcodes b
                            ON d.idMainDocTS = b.idMainDocTS
                    WHERE d.regNum IN ({doc_numbers_str})'
            )
        """
        cursor.execute(query)
        results = cursor.fetchall()
        res = {}
        for row in results:
            res[row[0]] = row[1]
        return res


def fox_get_object_persons(input_number: str | int, obj_type_id: int, biblio_code: str) -> list[dict]:
    """
    Отримує інформацію з АС Винаходи стосовно завників, винахідників та власників.

    В залежності від бібліографічного коду у параметр input_number необхідно передавати:
     - номер заявки (для отримання даних заявників, винахідників);
     - номер патенту (для отримання даних власників).
    """
    # Словник запитів у БД залежно від бібліографічного коду
    queries = {
        '71': 'EXEC [dbo].[ext_sis_getClaimApplicant] @InputNumber = %s, @PropertyType = %s',   # заявник
        '72': 'EXEC [dbo].[ext_sis_getClaimInventor] @InputNumber = %s, @PropertyType = %s',    # винахідник
        '73': 'EXEC [dbo].[ext_sis_getPatentOwner] @PatentNumber = %s, @PropertyType = %s',     # власник
    }

    # Коди типів об'єктів
    obj_types = {
        1: 'В',
        2: 'К',
        3: 'Т',
    }

    result = []

    with connections['vp3'].cursor() as cursor:
        cursor.setinputsizes([(pyodbc.SQL_VARCHAR, 255)])
        cursor.execute(queries[biblio_code], [input_number, obj_types[obj_type_id]])
        rows = cursor.fetchall()

        for item in rows:
            result.append({
                'name': item[0],
                'gov_code': item[1],
                'address': item[2],
                'country_code': item[3],
                'language_code': item[4],
                'enter_num': item[5],
            })

    return result


def fox_get_out_docs(app_number: str) -> list:
    with connections['ellav'].cursor() as cursor:
        query = f"""
            SELECT *
            FROM OPENQUERY([FOX,51433], '
                select
                    cd.NameWithIndex as docname,
                    ad1.value as datesend,
                    as1.value as regnum
                from
                    VP3.dbo.rr_exp_claim rc
                    join VP3.dbo.link_object lo on (
                      lo.idreestr1 = 204 and lo.idobject1 = rc.id
                      and lo.idreestr2 = 205 and lo.idlink = 105
                    )
                    join VP3.dbo.rr_document rd on (
                      rd.id = lo.idobject2
                    )
                    join VP3.dbo.cl_document cd on (
                      cd.id = rd.iddoctype
                    )
                    left join VP3.dbo.ap_date ad1 on (
                      ad1.idreestr = 205 and ad1.idobject = lo.idobject2 and ad1.idlink = 230
                    )
                    left join VP3.dbo.ap_date ai on (
                      ai.idreestr = 205 and ai.idobject = lo.idobject2 and ai.idlink = 417
                    )
                    left join VP3.dbo.ap_string as1 on (
                      as1.idreestr = 205 and as1.idobject = lo.idobject2 and as1.idlink = 229
                    )
                where
                    rc.inputNumber = ''{app_number}''
                    and ai.id is null
                            
                UNION
                
                select
                        cd.NameWithIndex as docname,
                        ad1.value as datesend,
                        as1.value as regnum
                from
                        VP3.dbo.rr_patent rc
                        join VP3.dbo.link_object lo on (
                            lo.idreestr1 = 224 and lo.idobject1 = rc.id
                            and lo.idreestr2 = 205 and lo.idlink = 105
                        )
                        join VP3.dbo.rr_document rd on (
                            rd.id = lo.idobject2
                        )
                        join VP3.dbo.cl_document cd on (
                            cd.id = rd.iddoctype
                        )
                        left join VP3.dbo.ap_date ad1 on (
                            ad1.idreestr = 205 and ad1.idobject = lo.idobject2 and ad1.idlink = 230
                        )
                        left join VP3.dbo.ap_date ai on (
                            ai.idreestr = 205 and ai.idobject = lo.idobject2 and ai.idlink = 417
                        )
                        left join VP3.dbo.ap_string as1 on (
                            as1.idreestr = 205 and as1.idobject = lo.idobject2 and as1.idlink = 229
                        )
                where
                        rc.inputNumber = ''{app_number}''
                        and ai.id is null
            ')
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results


class ClaimDataSource(ABC):
    """Отримує дані файлу формули."""

    @abstractmethod
    def get_claim_data(self) -> dict | None:
        pass


class K50ClaimDataSource(ClaimDataSource):
    """Отримує дані файлу формули з типом документа К50 (первинний документ)."""

    def __init__(self, application_number: str):
        self.application_number = application_number

    def get_claim_data(self) -> dict | None:
        query = f"""
            SELECT
                TOP 1 b_d.BlobPDF, b_d.LangDOC, e_a.FaktDate
            FROM
                ZayavkiDOC AS z_d
                INNER JOIN BlobDOC AS b_d 
                    ON z_d.idDoc = b_d.idDoc 
                INNER JOIN EArchive AS e_a 
                    ON e_a.idDoc = z_d.idDoc 
            WHERE
                z_d.ZayavkaNumber = '{self.application_number}' 
                AND z_d.DocTypeCODE IN ('К50', 'ДІ-3')
                AND b_d.BlobPDF IS NOT NULL
            ORDER BY e_a.FaktDate ASC
        """
        result = self._execute_query(query)

        if not result:
            return None

        return {
            'body': result[0],
            'language': result[1],
            'date': result[2],
            'file_type': 'pdf'
        }

    def _execute_query(self, query: str) -> tuple:
        with connections['e_archive'].cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return result


class C6ClaimDataSource(ClaimDataSource):
    """Отримує дані файлу формули з типом документа C6 (формула експертизи)."""

    def __init__(self, application_number: str, publication_date: datetime.date):
        self.application_number = application_number
        self.publication_date = publication_date

    def get_claim_data(self) -> dict | None:
        query = f"""
            SELECT *
            FROM OPENQUERY([FOX,51433], '
                SELECT TOP 1 CAST(body AS varbinary(max)) AS body, language, operdate
                FROM (
                    SELECT CAST(body AS varbinary(max)) AS body, language, operdate
                    FROM FOR3.dbo.rr_for
                    WHERE idDocType = 583 
                      AND InputNumber = ''{self.application_number}'' 
                      AND operdate < ''{self.publication_date}''

                    UNION ALL

                    SELECT CAST(body AS varbinary(max)) AS body, language, operdate
                    FROM FOR3.dbo.rr_for_archive
                    WHERE idDocType = 583 
                      AND InputNumber = ''{self.application_number}'' 
                      AND operdate < ''{self.publication_date}''
                ) AS combined
                ORDER BY operdate DESC;
            ');
        """
        result = self._execute_query(query)

        if not result:
            return None

        return {
            'body': result[0],
            'language': result[1],
            'date': result[2],
            'file_type': 'doc'
        }

    def _execute_query(self, query: str) -> tuple:
        with connections['e_archive'].cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return result


class ClaimDataSourceFactory:
    DATE_SWITCH = datetime.date(2023, 5, 24)  # Дата, до якої необхідно отримувати документ К50, а після - С6

    def create(self, application_number: str, publication_date: datetime.date) -> ClaimDataSource:
        if publication_date < ClaimDataSourceFactory.DATE_SWITCH:
            return K50ClaimDataSource(application_number)
        return C6ClaimDataSource(application_number, publication_date)


class FileConverter(ABC):

    @abstractmethod
    def convert(self, body: bytes) -> bytes:
        pass


class DocToPdfConverter(FileConverter):

    def convert(self, body: bytes) -> bytes:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Генерація унікальних імен файлів
            uid = uuid.uuid4().hex
            input_path = tmpdir_path / f"{uid}.doc"
            output_path = tmpdir_path / f"{uid}.pdf"

            input_path.write_bytes(body)

            # Конвертація LibreOffice
            result = subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(tmpdir_path),
                    str(input_path),
                ],
                capture_output=True,
                text=True,
            )

            # if result.returncode != 0:
            #     raise RuntimeError(f"LibreOffice failed: {result.stderr}")

            # Повернення PDF як bytes
            return output_path.read_bytes()


class FileConverterFactory:

    def create(self, file_type: str) -> FileConverter:
        if file_type == 'doc':
            return DocToPdfConverter()
        else:
            raise ValueError(f"Unsupported file type: {file_type}")


class TextExtractor(ABC):

    @abstractmethod
    def extract(self, body: bytes) -> str:
        pass


class TextFromPdfExtractor(TextExtractor):

    def extract(self, body: bytes) -> str:
        pdf_file = io.BytesIO(body)
        reader = PdfReader(pdf_file)

        result = ''
        for page in reader.pages:
            text = page.extract_text()
            if text:
                result += text + ' '

        return result.strip()


class TextExtractorFactory:

    def create(self, file_type: str) -> TextExtractor:
        if file_type == 'pdf':
            return TextFromPdfExtractor()
        else:
            raise ValueError(f"Unsupported file type: {file_type}")


class ApplicationGetClaimService:
    def __init__(
            self,
            application_number: str,
            publication_date: datetime.date,
            source_factory: ClaimDataSourceFactory,
            converter_factory: FileConverterFactory,
            text_extractor_factory: TextExtractorFactory
    ):
        self.application_number = application_number
        self.publication_date = publication_date
        self.source = source_factory.create(application_number, publication_date)
        self.converter_factory = converter_factory
        self.text_extractor_factory = text_extractor_factory

    @lru_cache(maxsize=32)
    def process_claim(self) -> dict | None:

        # Отримання даних
        claim_data = self.source.get_claim_data()

        if not claim_data:  # не знайдено документ формули
            return None

        # Конвертація у pdf (за необхідності)
        if claim_data['file_type'] != 'pdf':
            converter = self.converter_factory.create(claim_data['file_type'])
            body = converter.convert(claim_data['body'])
        else:
            body = claim_data['body']

        # Отримання тексту
        text_extractor = self.text_extractor_factory.create('pdf')
        text = text_extractor.extract(body)

        return {
            'date': claim_data['date'],
            'language': claim_data['language'],
            'body': body,
            'text': text
        }


class DrawingSource(ABC):
    application_number: str

    def __init__(self, application_number: str):
        self.application_number = application_number

    @abstractmethod
    def get_image(self) -> bytes:
        pass


class DrawingSourceVP3(DrawingSource):
    def get_image(self) -> bytes | None:
        query = f"""
            SELECT *
            FROM OPENQUERY([FOX,51433], '
                select db.body
                from VP3.dbo.rr_exp_claim c
                join VP3.dbo.link_object l on l.idReestr1 = 204 and l.idReestr2 = 205 and l.idObject1 = c.id
                join VP3.dbo.rr_document d on d.id = l.idObject2
                join VP3.dbo.cl_document cd on cd.id = d.idDocType
                join VP3.dbo.link_document_body lb on lb.idReestr = 205 and lb.idObject = d.id
                join VP3.dbo.rr_document_body db on db.id = lb.idBody
                where c.inputNumber = ''{self.application_number}'' 
                    and cd.shortName = ''С7А''
            ');
        """
        with connections['ellav'].cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result and result[0] else None


class DrawingSourceFactory:
    @staticmethod
    def create(application_number: str) -> DrawingSource:
        return DrawingSourceVP3(application_number)


class ApplicationGetDrawingService:
    """Сервіс отримує бінарні дані документа C7A (головне креслення)."""
    def __init__(self, application_number: str, source_factory: Type[DrawingSourceFactory]):
        self.application_number = application_number
        self.source_factory = source_factory

    def get_image(self) -> bytes | None:
        data_source = self.source_factory.create(self.application_number)
        return data_source.get_image()
