from abc import ABC, abstractmethod

from apps.search.mixins import BiblioDataInvUMLDRawGetMixin
from apps.search.models import AppLimited


class ApplicationRawDataFilter(ABC):
    """Абстрактный класс фильтра сырых данных."""

    @abstractmethod
    def filter_data(self, data: dict) -> None:
        pass


class ApplicationRawDataTMLimitedFilter(ApplicationRawDataFilter):
    """Фильтрует сырые данные ТМ в случае если она является ограниченной для публикации."""

    def _filter_limited_bibliography(self, biblio_data: dict, limited_settings: dict) -> None:
        """Фільтрує бібліографічні дані обмежених публікацій."""
        if 'ApplicantDetails' in biblio_data and not limited_settings.get('ApplicantDetails', False):
            del biblio_data['ApplicantDetails']
        if 'HolderDetails' in biblio_data and not limited_settings.get('HolderDetails', False):
            del biblio_data['HolderDetails']
        if 'RepresentativeDetails' in biblio_data \
                and not limited_settings.get('RepresentativeDetails', True):
            del biblio_data['RepresentativeDetails']
        if 'CorrespondenceAddress' in biblio_data and not limited_settings.get('CorrespondenceAddress', False):
            del biblio_data['CorrespondenceAddress']
        if 'GoodsServicesDetails' in biblio_data and not limited_settings.get('GoodsServicesDetails', True):
            del biblio_data['GoodsServicesDetails']
        if 'MarkImageDetails' in biblio_data:
            if 'MarkImageColourClaimedText' in biblio_data['MarkImageDetails']['MarkImage'] \
                    and not limited_settings.get('MarkImageColourClaimedText', False):
                del biblio_data['MarkImageDetails']['MarkImage']['MarkImageColourClaimedText']
            if 'MarkImageFilename' in biblio_data['MarkImageDetails']['MarkImage'] \
                    and not limited_settings.get('MarkImageFilename', False):
                del biblio_data['MarkImageDetails']['MarkImage']['MarkImageFilename']

    def _filter_limited_transactions(self, transactions: list, limited_settings: dict) -> None:
        """Фільтрує дані сповіщень обмежених публікацій."""
        for transaction in transactions:
            if 'TransactionBody' in transaction:
                transaction_body = transaction['TransactionBody']
                if 'ApplicantDetails' in transaction_body and not limited_settings.get('ApplicantDetails', False):
                    del transaction_body['ApplicantDetails']
                if 'HolderDetails' in transaction_body and not limited_settings.get('HolderDetails', False):
                    del transaction_body['HolderDetails']
                if 'RepresentativeDetails' in transaction_body \
                        and not limited_settings.get('RepresentativeDetails', True):
                    del transaction_body['RepresentativeDetails']
                if 'CorrespondenceAddress' in transaction_body \
                        and not limited_settings.get('CorrespondenceAddress', False):
                    del transaction_body['CorrespondenceAddress']
                if 'GoodsServicesDetails' in transaction_body \
                        and not limited_settings.get('GoodsServicesDetails', True):
                    del transaction_body['GoodsServicesDetails']

    def filter_data(self, data: dict) -> None:
        if data['Document'].get('is_limited'):
            limited_app = AppLimited.objects.filter(
                app_number=data['TradeMark']['TrademarkDetails']['ApplicationNumber'],
                obj_type_id=data['Document']['idObjType']
            ).first()
            self._filter_limited_bibliography(data['TradeMark']['TrademarkDetails'], limited_app.settings_dict)
            if 'Transactions' in data['TradeMark'] and 'Transaction' in data['TradeMark']['Transactions']:
                self._filter_limited_transactions(
                    data['TradeMark']['Transactions']['Transaction'],
                    limited_app.settings_dict
                )


class ApplicationRawDataIDLimitedFilter(ApplicationRawDataFilter):
    """Фильтрует сырые данные ТМ в случае если она является ограниченной для публикации."""

    def _filter_limited_bibliography(self, biblio_data: dict) -> None:
        """Фільтрує бібліографічні дані обмежених публікацій."""
        if 'ApplicantDetails' in biblio_data:
            del biblio_data['ApplicantDetails']

        if 'DesignerDetails' in biblio_data:
            del biblio_data['DesignerDetails']

        if 'HolderDetails' in biblio_data:
            del biblio_data['HolderDetails']

        if 'CorrespondenceAddress' in biblio_data:
            del biblio_data['CorrespondenceAddress']

        if 'DesignSpecimenDetails' in biblio_data:
            del biblio_data['DesignSpecimenDetails']

    def _filter_limited_transactions(self, transactions: list) -> None:
        """Фільтрує дані сповіщень обмежених публікацій."""
        for transaction in transactions:
            if 'TransactionBody' in transaction:
                transaction_body = transaction['TransactionBody']
                if 'DesignerDetails' in transaction_body:
                    del transaction_body['DesignerDetails']
                if 'HolderDetails' in transaction_body:
                    del transaction_body['HolderDetails']
                if 'CorrespondenceAddress' in transaction_body:
                    del transaction_body['CorrespondenceAddress']
                if 'DesignSpecimenDetails' in transaction_body:
                    del transaction_body['DesignSpecimenDetails']

    def filter_data(self, data: dict) -> None:
        if data['Document'].get('is_limited'):
            self._filter_limited_bibliography(data['Design']['DesignDetails'])
            if 'Transactions' in data['Design'] and 'Transaction' in data['Design']['Transactions']:
                self._filter_limited_transactions(
                    data['Design']['Transactions']['Transaction']
                )


class ApplicationRawDataInvUMLDLimitedFilter(ApplicationRawDataFilter, BiblioDataInvUMLDRawGetMixin):
    """Фильтрует сырые данные изобретения, полезной модели, топографии
     в случае если она является ограниченной для публикации."""

    def filter_data(self, data: dict) -> None:
        if data['Document'].get('is_limited'):
            biblio_data = self.get_biblio_data(data)

            limited_app = AppLimited.objects.filter(
                app_number=biblio_data['I_21'],
                obj_type_id=data['Document']['idObjType']
            ).first()

            if 'AB' in biblio_data and not limited_app.settings_dict.get('AB', False):
                del biblio_data['AB']
            if 'CL' in biblio_data and not limited_app.settings_dict.get('CL', False):
                del biblio_data['CL']
            if 'DE' in biblio_data and not limited_app.settings_dict.get('DE', False):
                del biblio_data['DE']
            if 'I_71' in biblio_data and not limited_app.settings_dict.get('I_71', False):
                del biblio_data['I_71']
            if 'I_72' in biblio_data and not limited_app.settings_dict.get('I_72', False):
                del biblio_data['I_72']
            if 'I_73' in biblio_data and not limited_app.settings_dict.get('I_73', False):
                del biblio_data['I_73']
            if 'I_98' in biblio_data and not limited_app.settings_dict.get('I_98', False):
                del biblio_data['I_98']
            if 'I_98_Index' in biblio_data and not limited_app.settings_dict.get('I_98_Index', False):
                del biblio_data['I_98_Index']


class ApplicationRawDataCRLimitedFilter(ApplicationRawDataFilter):
    """Фильтрует сырые данные авторского права в случае если оно является ограниченным для публикации."""

    def filter_data(self, data: dict) -> None:
        if data['Document'].get('is_limited'):
            limited_app = AppLimited.objects.filter(
                app_number=data['Certificate']['CopyrightDetails']['ApplicationNumber'],
                obj_type_id=data['Document']['idObjType']
            ).first()

            biblio_data = data['Certificate']['CopyrightDetails']
            if 'AuthorDetails' in biblio_data and not limited_app.settings_dict.get('AuthorDetails', False):
                del biblio_data['AuthorDetails']
            if 'Annotation' in biblio_data and not limited_app.settings_dict.get('Annotation', False):
                del biblio_data['Annotation']
            if 'ApplicantDetails' in biblio_data and not limited_app.settings_dict.get('ApplicantDetails', False):
                del biblio_data['ApplicantDetails']
            if 'CopyrightObjectKindDetails' in biblio_data \
                    and not limited_app.settings_dict.get('CopyrightObjectKindDetails', False):
                del biblio_data['CopyrightObjectKindDetails']
            if 'EmployerDetails' in biblio_data and not limited_app.settings_dict.get('EmployerDetails', False):
                del biblio_data['EmployerDetails']
            if 'HolderDetails' in biblio_data and not limited_app.settings_dict.get('HolderDetails', False):
                del biblio_data['HolderDetails']
            if 'PromulgationData' in biblio_data and not limited_app.settings_dict.get('PromulgationData', False):
                del biblio_data['PromulgationData']
            if 'RepresentativeDetails' in biblio_data \
                    and not limited_app.settings_dict.get('RepresentativeDetails', False):
                del biblio_data['RepresentativeDetails']
            if 'Name' in biblio_data and not limited_app.settings_dict.get('Name', True):
                del biblio_data['Name']
            if 'NameShort' in biblio_data and not limited_app.settings_dict.get('NameShort', True):
                del biblio_data['NameShort']


class ApplicationRawDataDecisionLimitedFilter(ApplicationRawDataFilter):
    """Фильтрует сырые данные договора авторского права в случае если оно является ограниченным для публикации."""

    def filter_data(self, data: dict) -> None:
        if data['Document'].get('is_limited'):
            limited_app = AppLimited.objects.filter(
                app_number=data['Decision']['DecisionDetails']['ApplicationNumber'],
                obj_type_id=data['Document']['idObjType']
            ).first()

            biblio_data = data['Decision']['DecisionDetails']

            # Поля, которые по умолчанию сохраняются
            if 'RegistrationNumber' in biblio_data and not limited_app.settings_dict.get('RegistrationNumber', True):
                del biblio_data['RegistrationNumber']
            if 'RegistrationDate' in biblio_data and not limited_app.settings_dict.get('RegistrationDate', True):
                del biblio_data['RegistrationDate']
            if 'PublicationDetails' in biblio_data and not limited_app.settings_dict.get('PublicationDetails', True):
                del biblio_data['PublicationDetails']
            if 'Name' in biblio_data and not limited_app.settings_dict.get('Name', True):
                del biblio_data['Name']
            if 'NameShort' in biblio_data and not limited_app.settings_dict.get('NameShort', True):
                del biblio_data['NameShort']

            # Поля, которые по умолчанию удаляются
            if 'Annotation' in biblio_data and not limited_app.settings_dict.get('Annotation', False):
                del biblio_data['Annotation']
            if 'ApplicantDetails' in biblio_data and not limited_app.settings_dict.get('ApplicantDetails', False):
                del biblio_data['ApplicantDetails']
            if 'ApplicationDate' in biblio_data and not limited_app.settings_dict.get('ApplicationDate', False):
                del biblio_data['ApplicationDate']
            if 'ApplicationNumber' in biblio_data and not limited_app.settings_dict.get('ApplicationNumber', False):
                del biblio_data['ApplicationNumber']
            if 'AuthorDetails' in biblio_data and not limited_app.settings_dict.get('AuthorDetails', False):
                del biblio_data['AuthorDetails']
            if 'CopyrightObjectKindDetails' in biblio_data \
                    and not limited_app.settings_dict.get('CopyrightObjectKindDetails', False):
                del biblio_data['CopyrightObjectKindDetails']
            if 'DocFlow' in biblio_data and not limited_app.settings_dict.get('DocFlow', False):
                del biblio_data['DocFlow']
            if 'LicenseeDetails' in biblio_data:
                if not limited_app.settings_dict.get('LicenseeDetails', False):
                    del biblio_data['LicenseeDetails']
                else:
                    for item in biblio_data['LicenseeDetails']['Licensee']:
                        if not limited_app.settings_dict['LicenseeDetails']['Address']:
                            del item['LicenseeAddressBook']['FormattedNameAddress']['Address']
                        if not limited_app.settings_dict['LicenseeDetails']['Name']:
                            del item['LicenseeAddressBook']['FormattedNameAddress']['Name']
            if 'LicensorDetails' in biblio_data:
                if not limited_app.settings_dict.get('LicensorDetails', False):
                    del biblio_data['LicensorDetails']
                else:
                    for item in biblio_data['LicensorDetails']['Licensor']:
                        if not limited_app.settings_dict['LicensorDetails']['Address']:
                            del item['LicensorAddressBook']['FormattedNameAddress']['Address']
                        if not limited_app.settings_dict['LicensorDetails']['Name']:
                            del item['LicensorAddressBook']['FormattedNameAddress']['Name']
            if 'RegistrationKind' in biblio_data and not limited_app.settings_dict.get('RegistrationKind', False):
                del biblio_data['RegistrationKind']
            if 'RegistrationKindCode' in biblio_data \
                    and not limited_app.settings_dict.get('RegistrationKindCode', False):
                del biblio_data['RegistrationKindCode']
            if 'RepresentativeDetails' in biblio_data \
                    and not limited_app.settings_dict.get('RepresentativeDetails', False):
                del biblio_data['RepresentativeDetails']
