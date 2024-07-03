from abc import ABC, abstractmethod
import datetime
import re

from apps.search.mixins import BiblioDataInvUMLDRawGetMixin, BiblioDataCRRawGetMixin
from apps.search.services.external import cead_get_id_doc


class ApplicationRawDataFixer(ABC):
    """Абстрактный класс сервиса исправления данных заявки."""

    @abstractmethod
    def fix_data(self, app_data: dict) -> None:
        pass


class ApplicationRawDataFSTMFixer(ApplicationRawDataFixer):
    """Сервис исправления данных заявки на ТМ, которые были получены с файловой системы."""

    def _fix_files_path(self, app_data: dict):
        app_data['Document']['filesPath'] = app_data['Document']['filesPath'].replace(
            'e:\\poznach_test_sis\\bear_tmpp_sis',
            '\\\\bear\\share'
        )
        if app_data['Document']['filesPath'][len(app_data['Document']['filesPath']) - 1] != '\\':
            app_data['Document']['filesPath'] = f"{app_data['Document']['filesPath']}\\"

    def _fix_sections(self, app_data: dict):
        """Исправляет структуру словаря."""
        if 'PaymentDetails' in app_data:
            app_data['TradeMark']['PaymentDetails'] = app_data['PaymentDetails']
            del app_data['PaymentDetails']

        if 'DocFlow' in app_data:
            app_data['TradeMark']['DocFlow'] = app_data['DocFlow']
            del app_data['DocFlow']

        if 'Transactions' in app_data:
            app_data['TradeMark']['Transactions'] = app_data['Transactions']
            del app_data['Transactions']

    def _fix_publication(self, app_data: dict):
        """Исправляет данные и структуру данных публикации."""
        try:
            if app_data['TradeMark']['TrademarkDetails'].get('PublicationDetails', {}).get('Publication'):
                # Исправление даты публикации, структуры
                try:
                    d = datetime.datetime.today().strptime(
                        app_data['TradeMark']['TrademarkDetails']['PublicationDetails']['Publication']['PublicationDate'],
                        '%d.%m.%Y'
                    )
                except ValueError:
                    pass
                else:
                    app_data['TradeMark']['TrademarkDetails']['PublicationDetails']['Publication']['PublicationDate'] \
                        = d.strftime('%Y-%m-%d')
                app_data['TradeMark']['TrademarkDetails']['PublicationDetails'] = [
                    app_data['TradeMark']['TrademarkDetails']['PublicationDetails']['Publication']
                ]

                # Исправление номера бюлетеня
                for x in app_data['TradeMark']['TrademarkDetails']['PublicationDetails']:
                    if len(x.get('PublicationIdentifier')) < 6:
                        x['PublicationIdentifier'] = f"{x['PublicationIdentifier']}/{x['PublicationDate'][:4]}"
        except AttributeError:
            pass

    def _fix_holder_original(self, app_data: dict):
        """Исправляет данные оригинальных наименований и адресов владельцев."""
        if 'HolderDetails' in app_data['TradeMark']['TrademarkDetails']:
            for holder in app_data['TradeMark']['TrademarkDetails']['HolderDetails']['Holder']:
                formatted_name_address = holder['HolderAddressBook']['FormattedNameAddress']
                is_ua = formatted_name_address['Address']['AddressCountryCode'] == 'UA'
                if 'FreeFormatAddressLineOriginal' in formatted_name_address['Address']['FreeFormatAddress']:
                    if is_ua or formatted_name_address['Address']['FreeFormatAddress'][
                        'FreeFormatAddressLineOriginal'] == '':
                        del formatted_name_address['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal']
                if 'FreeFormatNameLineOriginal' in formatted_name_address['Address']['FreeFormatAddress']:
                    if is_ua or formatted_name_address['Address']['FreeFormatAddress'][
                        'FreeFormatNameLineOriginal'] == '':
                        del formatted_name_address['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal']
                if 'FreeFormatNameLineOriginal' in formatted_name_address['Name']['FreeFormatName'][
                    'FreeFormatNameDetails']:
                    if is_ua or \
                            formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails'][
                                'FreeFormatNameLineOriginal'] == '':
                        del formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails'][
                            'FreeFormatNameLineOriginal']

    def _fix_applicant_original(self, app_data: dict):
        """Исправляет данные оригинальных наименований и адресов владельцев."""
        if 'ApplicantDetails' in app_data['TradeMark']['TrademarkDetails']:
            for applicant in app_data['TradeMark']['TrademarkDetails']['ApplicantDetails']['Applicant']:
                formatted_name_address = applicant['ApplicantAddressBook']['FormattedNameAddress']
                is_ua = formatted_name_address['Address']['AddressCountryCode'] == 'UA'
                if 'FreeFormatAddressLineOriginal' in formatted_name_address['Address']['FreeFormatAddress']:
                    if is_ua or formatted_name_address['Address']['FreeFormatAddress'][
                        'FreeFormatAddressLineOriginal'] == '':
                        del formatted_name_address['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal']
                if 'FreeFormatNameLineOriginal' in formatted_name_address['Address']['FreeFormatAddress']:
                    if is_ua or formatted_name_address['Address']['FreeFormatAddress'][
                        'FreeFormatNameLineOriginal'] == '':
                        del formatted_name_address['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal']
                if 'FreeFormatNameLineOriginal' in formatted_name_address['Name']['FreeFormatName'][
                    'FreeFormatNameDetails']:
                    if is_ua or \
                            formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails'][
                                'FreeFormatNameLineOriginal'] == '':
                        del formatted_name_address['Name']['FreeFormatName']['FreeFormatNameDetails'][
                            'FreeFormatNameLineOriginal']

    def _fix_stages(self, app_data: dict):
        """Исправляет секцию стадий заявки."""
        if app_data['TradeMark']['TrademarkDetails'].get('stages'):
            app_data['TradeMark']['TrademarkDetails']['stages'] = app_data['TradeMark']['TrademarkDetails']['stages'][::-1]
            # Если есть охранный документ, то все стадии д.б. done
            if app_data['TradeMark']['TrademarkDetails'].get('RegistrationNumber'):
                for stage in app_data['TradeMark']['TrademarkDetails']['stages']:
                    stage['status'] = 'done'

    def _fix_associated_registration_details(self, app_data: dict):
        if app_data['TradeMark']['TrademarkDetails'].get(
                'AssociatedRegistrationApplicationDetails', {}
        ).get(
            'AssociatedRegistrationApplication', {}
        ).get(
            'AssociatedRegistrationDetails', {}
        ).get(
            'DivisionalApplication'
        ):
            for app in app_data['TradeMark']['TrademarkDetails']['AssociatedRegistrationApplicationDetails'][
                'AssociatedRegistrationApplication']['AssociatedRegistrationDetails']['DivisionalApplication']:
                try:
                    app['AssociatedRegistration']['AssociatedRegistrationDate'] = datetime.datetime.strptime(
                        app['AssociatedRegistration']['AssociatedRegistrationDate'], '%d.%m.%Y'
                    ).strftime('%Y-%m-%d')
                except:
                    pass

    def _fix_termination_date(self, app_data: dict):
        if app_data['TradeMark']['TrademarkDetails'].get('TerminationDate'):
            try:
                app_data['TradeMark']['TrademarkDetails']['TerminationDate'] = datetime.datetime.strptime(
                    app_data['TradeMark']['TrademarkDetails']['TerminationDate'], '%d.%m.%Y'
                ).strftime('%Y-%m-%d')
            except:
                pass

    def _fix_exhibition_termination_date(self, app_data: dict):
        if 'ExhibitionPriorityDetails' in app_data['TradeMark']['TrademarkDetails'] \
                and type(app_data['TradeMark']['TrademarkDetails']['ExhibitionPriorityDetails']) == list:
            app_data['TradeMark']['TrademarkDetails']['ExhibitionPriorityDetails'] = {
                'ExhibitionPriority': app_data['TradeMark']['TrademarkDetails']['ExhibitionPriorityDetails']
            }

    def _fix_transactions(self, app_data: dict):
        if app_data['TradeMark'].get('Transactions', {}).get('Transaction'):
            # Удаление чужих оповещений
            app_data['TradeMark']['Transactions']['Transaction'] = list(filter(
                lambda x: x.get('@registrationNumber') == app_data['TradeMark']['TrademarkDetails'].get(
                    'RegistrationNumber'),
                app_data['TradeMark']['Transactions']['Transaction']
            ))

            for transaction in app_data['TradeMark']['Transactions']['Transaction']:
                # fix структуры
                if 'TransactionBody' in transaction:
                    if 'PublicationDate' in transaction['TransactionBody'] \
                            or 'PublicationNumber' in transaction['TransactionBody']:
                        transaction['TransactionBody']['PublicationDetails'] = {
                            'Publication': {
                                'PublicationDate': transaction['TransactionBody'].pop('PublicationDate', None),
                                'PublicationNumber': transaction['TransactionBody'].pop('PublicationNumber', None),
                            }
                        }

                    # fix дат
                    try:
                        d = transaction['TransactionBody']['PublicationDetails']['Publication'][
                            'PublicationDate']
                        transaction['TransactionBody']['PublicationDetails']['Publication'][
                            'PublicationDate'] = datetime.datetime.strptime(d, '%d.%m.%Y').strftime('%Y-%m-%d')
                    except:
                        pass
                    try:
                        d = transaction['TransactionBody']['RegisterDate']
                        transaction['TransactionBody']['RegisterDate'] = datetime.datetime.strptime(
                            d, '%d.%m.%Y'
                        ).strftime('%Y-%m-%d')
                    except:
                        pass

    def _fix_id_doc_cead(self, app_data: dict):
        """Получает idDocCead из БД EArchive, если он отсутсвует в JSON."""
        if app_data['TradeMark'].get('DocFlow', {}).get('Documents', []):
            for doc in app_data['TradeMark']['DocFlow']['Documents']:
                if not doc['DocRecord'].get('DocIdDocCEAD') and doc['DocRecord'].get('DocBarCode'):
                    id_doc_cead = cead_get_id_doc(doc['DocRecord']['DocBarCode'])
                    if id_doc_cead:
                        doc['DocRecord']['DocIdDocCEAD'] = id_doc_cead

    def fix_data(self, app_data: dict) -> None:
        self._fix_files_path(app_data)
        self._fix_sections(app_data)
        self._fix_publication(app_data)
        self._fix_applicant_original(app_data)
        self._fix_holder_original(app_data)
        self._fix_stages(app_data)
        self._fix_associated_registration_details(app_data)
        self._fix_termination_date(app_data)
        self._fix_exhibition_termination_date(app_data)
        self._fix_transactions(app_data)
        self._fix_id_doc_cead(app_data)


class ApplicationRawDataFSIDFixer(ApplicationRawDataFixer):
    """Исправляет данные промышленного образца, которые были получены с файловой системы."""

    def _fix_files_path(self, app_data: dict):
        if app_data['Document']['filesPath'][len(app_data['Document']['filesPath']) - 1] != '\\':
            app_data['Document']['filesPath'] = f"{app_data['Document']['filesPath']}\\"

    def _fix_indication_details(self, app_data: dict):
        """Исправляет формат МКПЗ"""
        for item in app_data['Design']['DesignDetails'].get('IndicationProductDetails', []):
            cl = item.get('Class')
            if cl:
                cl = cl.replace('.', '-')
                cl_l = cl.split('-')
                if len(cl_l[1]) == 1:
                    cl_l[1] = f"0{cl_l[1]}"
                item['Class'] = '-'.join(cl_l)

    def _fix_sections(self, app_data: dict):
        """Исправляет случай если секции PaymentDetails, DocFlow, Transactions не попали в секцию Design."""
        if 'PaymentDetails' in app_data:
            app_data['Design']['PaymentDetails'] = app_data['PaymentDetails']
            del app_data['PaymentDetails']

        if 'DocFlow' in app_data:
            app_data['Design']['DocFlow'] = app_data['DocFlow']
            del app_data['DocFlow']

        if 'Transactions' in app_data:
            app_data['Design']['Transactions'] = app_data['Transactions']
            del app_data['Transactions']

    def _fix_publication_details(self, app_data: dict):
        """Приведение номеря бюлетня к формату "bul_num/YYYY"""
        if app_data['Design']['DesignDetails'].get('RecordPublicationDetails'):
            for item in app_data['Design']['DesignDetails']['RecordPublicationDetails']:
                if len(item.get('PublicationIdentifier')) < 6:
                    item['PublicationIdentifier'] = f"{item['PublicationIdentifier']}/{item['PublicationDate'][:4]}"

    def _fix_stages(self, app_data: dict):
        if app_data['Design']['DesignDetails'].get('stages'):
            app_data['Design']['DesignDetails']['stages'] = app_data['Design']['DesignDetails']['stages'][::-1]
            # Если есть охранный документ, то все стадии д.б. done
            if 'RegistrationNumber' in app_data['Design']['DesignDetails']:
                for stage in app_data['Design']['DesignDetails']['stages']:
                    stage['status'] = 'done'

    def _fix_priority_date(self, app_data: dict):
        try:
            if app_data['Design']['DesignDetails'].get('PriorityDetails', {}).get('Priority'):
                for item in app_data['Design']['DesignDetails']['PriorityDetails']['Priority']:
                    if not item['PriorityDate']:
                        del item['PriorityDate']
        except AttributeError:
            pass

    def _fix_transactions(self, app_data: dict):
        if app_data['Design'].get('Transactions', {}).get('Transaction'):
            # Удаление чужих оповещений
            app_data['Design']['Transactions']['Transaction'] = list(filter(
                lambda x: x.get('@registrationNumber') == app_data['Design']['DesignDetails'].get('RegistrationNumber'),
                app_data['Design']['Transactions']['Transaction']
            ))

            # fix дат
            for transaction in app_data['Design']['Transactions']['Transaction']:
                try:
                    d = transaction['TransactionBody']['PublicationDetails']['Publication']['PublicationDate']
                    transaction['TransactionBody']['PublicationDetails']['Publication'][
                        'PublicationDate'] = datetime.datetime.strptime(d, '%d.%m.%Y').strftime('%Y-%m-%d')
                except:
                    pass

    def _fix_id_doc_cead(self, app_data: dict):
        """Получает idDocCead из БД EArchive, если он отсутсвует в JSON."""
        if app_data['Design'].get('DocFlow', {}).get('Documents', []):
            for doc in app_data['Design']['DocFlow']['Documents']:
                if not doc['DocRecord'].get('DocIdDocCEAD') and doc['DocRecord'].get('DocBarCode'):
                    id_doc_cead = cead_get_id_doc(doc['DocRecord']['DocBarCode'])
                    if id_doc_cead:
                        doc['DocRecord']['DocIdDocCEAD'] = id_doc_cead

    def fix_data(self, app_data: dict) -> None:
        self._fix_files_path(app_data)
        self._fix_indication_details(app_data)
        self._fix_sections(app_data)
        self._fix_publication_details(app_data)
        self._fix_stages(app_data)
        self._fix_priority_date(app_data)
        self._fix_transactions(app_data)
        self._fix_id_doc_cead(app_data)


class ApplicationRawDataFSInvUMLDFixer(ApplicationRawDataFixer, BiblioDataInvUMLDRawGetMixin):
    """Исправляет данные изобретения, полезной модели, топографии, которые были получены с файловой системы."""

    def _fix_i_71(self, biblio_data: dict) -> None:
        i_71 = biblio_data.get('I_71', [])
        if type(i_71) is dict:
            i_71 = biblio_data['I_71']['I_71.N']
        biblio_data['I_71'] = i_71

    def _fix_i_72(self, biblio_data: dict) -> None:
        for I_72 in biblio_data.get('I_72', []):
            if I_72.get('I_72.N'):
                I_72['I_72.N.E'] = I_72.pop('I_72.N')
            if I_72.get('I_72.C'):
                I_72['I_72.C.E'] = I_72.pop('I_72.C')

    def _fix_i_73(self, biblio_data: dict) -> None:
        i_73 = biblio_data.get('I_73', [])
        if type(i_73) is dict:
            i_73 = biblio_data['I_73']['I_73.N']

        for item_i_73 in i_73:
            if item_i_73.get('I_73.N.U'):
                item_i_73['I_73.N'] = item_i_73.pop('I_73.N.U')
            if item_i_73.get('I_73.N.R'):
                item_i_73['I_73.N'] = item_i_73.pop('I_73.N.R')
            if item_i_73.get('I_73.N.E'):
                item_i_73['I_73.N'] = item_i_73.pop('I_73.N.E')
            if item_i_73.get('I_73.C.U'):
                item_i_73['I_73.C'] = item_i_73.pop('I_73.C.U')
            if item_i_73.get('I_73.C.R'):
                item_i_73['I_73.C'] = item_i_73.pop('I_73.C.R')
            if item_i_73.get('I_73.C.E'):
                item_i_73['I_73.C'] = item_i_73.pop('I_73.C.E')
        biblio_data['I_73'] = i_73

    def _fix_i_98(self, biblio_data: dict) -> None:
        if biblio_data.get('I_98.Index') is not None:
            biblio_data['I_98_Index'] = biblio_data.pop('I_98.Index')

    def fix_transactions(self, app_data: dict) -> None:
        if app_data.get('TRANSACTIONS'):
            # Дополнительное поле с датой бюлетня для поиска по ней
            if type(app_data['TRANSACTIONS']['TRANSACTION']) is dict:
                app_data['TRANSACTIONS']['TRANSACTION'] = [app_data['TRANSACTIONS']['TRANSACTION']]
            for transaction in app_data['TRANSACTIONS']['TRANSACTION']:
                bul_date = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', transaction['BULLETIN'])
                try:
                    bul_date_groups = bul_date.groups()
                    d = f"{bul_date_groups[2]}-{bul_date_groups[1]}-{bul_date_groups[0]}"
                    transaction['BULLETIN_DATE'] = d
                except (ValueError, IndexError, AttributeError):  # Строка бюлетня не содержит дату
                    pass

    def fix_data(self, app_data: dict) -> None:
        biblio_data = self.get_biblio_data(app_data)
        self._fix_i_71(biblio_data)
        self._fix_i_72(biblio_data)
        self._fix_i_73(biblio_data)
        self._fix_i_98(biblio_data)
        self.fix_transactions(app_data)


class ApplicationRawDataFSMadridFixer(ApplicationRawDataFixer):
    def _fix_dates(self, biblio_data: dict) -> None:
        date_keys = ['@EXPDATE', '@NOTDATE', '@REGEDAT', '@REGRDAT', '@INTREGD']
        for key in date_keys:
            if biblio_data.get(key):
                biblio_data[key] = datetime.datetime.strptime(biblio_data[key], '%Y%m%d').strftime('%Y-%m-%d')

    def _fix_pub_date(self, biblio_data: dict) -> None:
        if biblio_data.get('ENN', {}).get('@PUBDATE'):
            try:
                biblio_data['ENN']['@PUBDATE'] = datetime.datetime.strptime(
                    biblio_data['ENN']['@PUBDATE'], '%Y%m%d'
                ).strftime('%Y-%m-%d')
            except ValueError:  # Дата уже в правильном формате
                pass

    def _fix_basappd(self, biblio_data: dict) -> None:
        if biblio_data.get('BASGR', {}).get('BASAPPGR', {}).get('BASAPPD'):
            biblio_data['BASGR']['BASAPPGR']['BASAPPD'] = datetime.datetime.strptime(
                biblio_data['BASGR']['BASAPPGR']['BASAPPD'], '%Y%m%d'
            ).strftime('%Y-%m-%d')

    def _fix_priappd(self, biblio_data: dict) -> None:
        if biblio_data.get('PRIGR', {}).get('PRIAPPD', {}):
            biblio_data['PRIGR']['PRIAPPD'] = datetime.datetime.strptime(
                biblio_data['PRIGR']['PRIAPPD'], '%Y%m%d'
            ).strftime('%Y-%m-%d')

    def fix_data(self, app_data: dict) -> None:
        self._fix_dates(app_data['MadridTradeMark']['TradeMarkDetails'])
        self._fix_pub_date(app_data['MadridTradeMark']['TradeMarkDetails'])
        self._fix_basappd(app_data['MadridTradeMark']['TradeMarkDetails'])
        self._fix_priappd(app_data['MadridTradeMark']['TradeMarkDetails'])


class ApplicationRawDataFSGeoFixer(ApplicationRawDataFixer):
    def _fix_product_description(self, app_data: dict) -> None:
        if 'ProductDescription' in app_data['Geo']['GeoDetails']:
            app_data['Geo']['GeoDetails']['ProductDesc'] = app_data['Geo']['GeoDetails'].pop('ProductDescription')

    def fix_data(self, app_data: dict) -> None:
        self._fix_product_description(app_data)


class ApplicationRawDataFSCRFixer(ApplicationRawDataFixer, BiblioDataCRRawGetMixin):

    def _fix_publication_date(self, biblio_data: dict) -> None:
        """Исправление формата даты PublicationDate."""
        if biblio_data.get('PublicationDetails', {}).get('Publication', {}).get('PublicationDate'):
            d = biblio_data['PublicationDetails']['Publication']['PublicationDate']
            biblio_data['PublicationDetails']['Publication']['PublicationDate'] = datetime.datetime.strptime(
                d, '%d.%m.%Y'
            ).strftime('%Y-%m-%d')

    def fix_data(self, app_data: dict) -> None:
        biblio_data = self.get_biblio_data(app_data)
        self._fix_publication_date(biblio_data)
