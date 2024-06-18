from abc import ABC, abstractmethod
import datetime

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
