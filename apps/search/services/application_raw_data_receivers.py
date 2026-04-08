from abc import ABC, abstractmethod
import json
import os
import logging
import datetime

from django.db import connections

from apps.search.models import IpcAppList, AppLimited
from apps.search.mixins import BiblioDataInvUMLDRawGetMixin
from apps.bulletin.services import bulletin_get_number_with_year_by_date, bulletin_get_number_by_date, \
    bulletin_get_date_by_num_and_year
from apps.bulletin.models import EBulletinData


# Get an instance of a logger
from apps.search.services.external import madrid_notif_get_ua_bul, fox_get_object_persons, \
    poznachennya_claim_get_termination_date

logger = logging.getLogger(__name__)


class ApplicationRawDataReceiver(ABC):
    """Абстрактный класс для получения сырых данных заявки."""

    _app: IpcAppList

    def __init__(self, app: IpcAppList):
        self._app = app

    @abstractmethod
    def get_data(self) -> dict:
        pass


class ApplicationRawDataFSReceiver(ApplicationRawDataReceiver):
    """Получает сырые данные заявки с файловой системы."""

    _file_path: str | None = None

    def _set_file_path(self) -> None:
        """Устанавливает путь к файлу JSON с данными объекта."""

        # Если путь к файлу указан сразу (случай с авторским правом)
        if '.json' in self._app.real_files_path:
            self._file_path = self._app.real_files_path
            return

        # Путь к файлу JSON с данными объекта:
        file_name = self._app.registration_number \
            if (self._app.registration_number and self._app.registration_number != '0') \
            else self._app.app_number
        file_name = file_name.replace('/', '_')

        file_path = os.path.join(self._app.real_files_path, f"{file_name}.json")

        # Случай если охранные документы имеют название заявки
        if not os.path.exists(file_path) and self._app.obj_type_id in (4, 5, 6):
            file_name = self._app.app_number.replace('/', '_')
            file_path = os.path.join(self._app.real_files_path, f"{file_name}.json")

        self._file_path = file_path

    def _read_data_from_file(self) -> dict:
        """Читает и возвращает данные из файла."""
        data = {}
        encodings = ['utf-8', 'utf-8-sig', 'utf-16']
        error = None

        for encoding in encodings:
            try:
                with open(self._file_path, 'r', encoding=encoding) as f:
                    file_content = f.read().encode()
                    file_content = file_content.replace(b'\xef\xbb\xbf', b'')
                    data = json.loads(file_content)
                    break  # Если успешно прочитали и распарсили, выходим из цикла
            except (UnicodeDecodeError, UnicodeError) as e:
                error = f"Unicode error with encoding {encoding}: {e}: {self._file_path}"
            except json.decoder.JSONDecodeError as e:
                error = f"JSONDecodeError with encoding {encoding}: {e}: {self._file_path}"
            except FileNotFoundError as e:
                error = f"FileNotFoundError: {e}"
                break  # Если файл не найден, нет смысла продолжать

        if not data and error:
            logger.error(error)

        return data

    def _set_is_limited(self, data: dict) -> None:
        """Проверяет является ли обїект ограниченной публикацией, устанавливает метку в данных об этом."""
        if data and AppLimited.objects.filter(app_number=self._app.app_number,
                                              obj_type_id=self._app.obj_type_id
                                              ).exclude(cancelled=True).exists():
            data['Document']['is_limited'] = True

    def get_data(self) -> dict:
        self._set_file_path()
        data = self._read_data_from_file()

        self._set_is_limited(data)

        return data


class ApplicationRawDataFSTMReceiver(ApplicationRawDataFSReceiver):
    """Получает сырые данные ТМ с файловой системы, получает доп. информацию, которой нет в ФС."""

    def _set_441(self, data: dict) -> None:
        """Устанавливает значение 441-го поля, если оно отсутствует в данных."""
        if data and not data['TradeMark']['TrademarkDetails'].get('Code_441'):
            bulletin_item = EBulletinData.objects.filter(
                app_number=data['TradeMark']['TrademarkDetails'].get('ApplicationNumber')
            ).first()
            if bulletin_item:
                data['TradeMark']['TrademarkDetails']['Code_441'] = bulletin_item.publication_date.strftime('%Y-%m-%d')
                data['TradeMark']['TrademarkDetails']['Code_441_BulNumber'] = bulletin_get_number_by_date(
                    bulletin_item.publication_date
                )

    def get_data(self) -> dict:
        data = super().get_data()

        self._set_441(data)

        return data


class ApplicationRawDataFSIDReceiver(ApplicationRawDataFSReceiver):
    """Получает сырые данные пром. образца с файловой системы, получает доп. информацию, которой нет в ФС."""
    def _set_expiry_date(self, data: dict) -> None:
        if data.get('Design', {}).get('DesignDetails', {}).get('RegistrationNumber'):
            query = """
                        SELECT i.data_json
                        FROM fv_claim_inid_item AS i
                        INNER JOIN fv_od AS od
                        ON od.claim_id = i.claim_id
                        INNER JOIN fv_claim AS cl
                        ON cl.id = i.claim_id
                        WHERE cl.type_code = 'PROM_ZNAK' AND i.inid_code = '18' AND od.reg_number = %s
                    """
            with connections['prod_erp_cms_claim'].cursor() as cursor:
                cursor.execute(query, [data['Design']['DesignDetails']['RegistrationNumber']])
                row = cursor.fetchone()
                if row:
                    expiry_data = json.loads(row[0])
                    data['Design']['DesignDetails']['ExpiryDate'] = expiry_data['date']

    def _set_termination_details(self, data: dict) -> None:
        """Встановлює дані щодо припинення дії реєстрації."""
        if data.get('Design', {}).get('DesignDetails', {}).get('registration_status_color') == 'red':
            if data.get('Transactions', {}).get('Transaction', []):
                # Пошук відповідного сповіщення (як правило, воно останнє)
                for transaction in data['Transactions']['Transaction'][::-1]:
                    if 'Termination' in transaction['@type']:
                        termination_details = {
                            'TerminationDate': transaction['TransactionBody']['TerminationDate'],
                            'PublicationDate': transaction['@bulletinDate'],
                            'PublicationIdentifier': f"{transaction['@bulletinNumber']}/"
                                                     f"{transaction['@bulletinDate'][:4]}"
                        }
                        data['Design']['DesignDetails']['TerminationDetails'] = termination_details
                        break

            # Отримання з АС "Позначення" якщо не вдалося заповнити даними зі сповіщення
            if 'TerminationDetails' not in data['Design']['DesignDetails']:
                termination_date = poznachennya_claim_get_termination_date(
                    data['Design']['DesignDetails']['DesignApplicationNumber'],
                    6
                )
                if termination_date:
                    termination_details = {
                        'TerminationDate': termination_date
                    }
                    data['Design']['DesignDetails']['TerminationDetails'] = termination_details

    def get_data(self) -> dict:
        data = super().get_data()
        self._set_expiry_date(data)
        self._set_termination_details(data)
        return data


class ApplicationRawDataFSInvUMLDReceiver(ApplicationRawDataFSReceiver, BiblioDataInvUMLDRawGetMixin):
    """Получает сырые данные изобретения, полезной модели, топографии с файловой системы,
    получает доп. информацию, которой нет в ФС."""

    def _set_i_43_bul_str(self, biblio_data: dict) -> None:
        if biblio_data.get('I_43.D'):
            i_43_d = biblio_data['I_43.D'][0]
            bull_str = bulletin_get_number_with_year_by_date(i_43_d)
            if bull_str:
                biblio_data['I_43_bul_str'] = bull_str

    def _set_i_45_bul_str(self, biblio_data: dict) -> None:
        if biblio_data.get('I_45.D'):
            i_45_d = biblio_data['I_45.D'][len(biblio_data['I_45.D']) - 1]
            bull_str = bulletin_get_number_with_year_by_date(i_45_d)
            if bull_str:
                biblio_data['I_45_bul_str'] = bull_str

    def _set_i_73(self, biblio_data: dict, obj_type_id: int) -> None:
        if biblio_data.get('I_11'):
            # Отримання списку власників з АС "Винаходи"
            holders = fox_get_object_persons(biblio_data['I_11'], obj_type_id, '73')
            if holders:
                result = []
                for holder in holders:
                    item = {}
                    if holder['name']:
                        item['I_73.N'] = holder['name'].strip()
                    if holder['gov_code']:
                        item['EDRPOU'] = holder['gov_code'].strip()
                    if holder['country_code']:
                        item['I_73.C'] = holder['country_code'].strip()
                    if holder['language_code']:
                        item['I_73.L'] = holder['language_code'].strip()
                    if holder['enter_num']:
                        item['I_73.O'] = int(holder['enter_num'])
                    result.append(item)
                biblio_data['I_73'] = result

    def get_data(self) -> dict:
        data = super().get_data()

        biblio_data = self.get_biblio_data(data)
        if biblio_data:
            self._set_i_43_bul_str(biblio_data)
            self._set_i_45_bul_str(biblio_data)
            self._set_i_73(biblio_data, data.get('Document', {}).get('idObjType'))

        return data


class ApplicationRawDataFSInvCertReceiver(ApplicationRawDataFSReceiver):
    pass


class ApplicationRawDataFSMadridReceiver(ApplicationRawDataFSReceiver):
    """Получает сырые данные международных ТМ, получает доп. информацию, которой нет в ФС."""
    def _set_441(self, data: dict) -> None:
        try:
            app = IpcAppList.objects.filter(
                obj_type_id=9,  # registration_date у заявки с этим obj_type_id и будет 441-м кодом
                app_number=self._app.app_number
            ).first()
            data['MadridTradeMark']['TradeMarkDetails']['Code_441'] = app.registration_date.strftime('%Y-%m-%d')
        except AttributeError:
            data['MadridTradeMark']['TradeMarkDetails']['Code_441'] = self._app.registration_date.strftime('%Y-%m-%d')

    def get_data(self) -> dict:
        data_from_file = super().get_data()

        if data_from_file:

            data = {
                'Document': {
                    'idObjType': self._app.obj_type_id,
                    'filesPath': self._app.files_path
                },
                'MadridTradeMark': {
                    'TradeMarkDetails': data_from_file
                }
            }

            self._set_441(data)

            return data

        return data_from_file


class ApplicationRawDataFSMadrid9Receiver(ApplicationRawDataFSMadridReceiver):
    """Получает сырые данные международных ТМ с распространением на территорию Украины,
    получает доп. информацию, которой нет в ФС."""
    pass


class ApplicationRawDataFSMadrid14Receiver(ApplicationRawDataFSMadridReceiver):
    """Получает сырые данные международных ТМ с распространением на территорию Украины,
    получает доп. информацию, которой нет в ФС."""

    def _set_ua_bul(self, data: dict) -> None:
        """Встановлює дані українського бюлетеня, у якому були опубліковані дані міжнародної реєстрації."""
        pubdate = datetime.datetime.strptime(
            data['MadridTradeMark']['TradeMarkDetails']['ENN']['@PUBDATE'], '%Y%m%d'
        ).strftime('%Y-%m-%d')
        ua_bul_number_year = madrid_notif_get_ua_bul(pubdate)
        if ua_bul_number_year:
            ua_bul_number_date = bulletin_get_date_by_num_and_year(ua_bul_number_year[0], ua_bul_number_year[1])
            data['MadridTradeMark']['TradeMarkDetails']['UkrainianBulletin'] = {
                'BulNumber': ua_bul_number_year[0],
                'BulYear': ua_bul_number_year[1],
                'BulDate': ua_bul_number_date
            }

    def get_data(self) -> dict:
        data = super().get_data()
        self._set_ua_bul(data)
        return data


class ApplicationRawDataFSGeoReceiver(ApplicationRawDataFSReceiver):
    """Получает сырые данные ГЗ,
    получает доп. информацию, которой нет в ФС."""
    pass


class ApplicationRawDataFSWKMReceiver(ApplicationRawDataFSReceiver):
    """Отримує сирі дані добре відомої ТМ."""

    def _set_file_path(self) -> None:
        """Встановлює шлях до файлу з даними."""
        self._file_path = os.path.join(self._app.real_files_path, f"{self._app.id_claim}.json")
