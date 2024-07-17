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

    def filter_data(self, data: dict) -> None:
        if data['Document'].get('is_limited'):
            if 'ApplicantDetails' in data['TradeMark']['TrademarkDetails']:
                del data['TradeMark']['TrademarkDetails']['ApplicantDetails']

            if 'HolderDetails' in data['TradeMark']['TrademarkDetails']:
                del data['TradeMark']['TrademarkDetails']['HolderDetails']

            if 'CorrespondenceAddress' in data['TradeMark']['TrademarkDetails']:
                del data['TradeMark']['TrademarkDetails']['CorrespondenceAddress']

            if 'MarkImageDetails' in data['TradeMark']['TrademarkDetails']:
                if 'MarkImageColourClaimedText' in data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']:
                    del data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']['MarkImageColourClaimedText']
                del data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']['MarkImageFilename']


class ApplicationRawDataIDLimitedFilter(ApplicationRawDataFilter):
    """Фильтрует сырые данные ТМ в случае если она является ограниченной для публикации."""

    def filter_data(self, data: dict) -> None:
        if data['Document'].get('is_limited'):
            if 'ApplicantDetails' in data['Design']['DesignDetails']:
                del data['Design']['DesignDetails']['ApplicantDetails']

            if 'DesignerDetails' in data['Design']['DesignDetails']:
                del data['Design']['DesignDetails']['DesignerDetails']

            if 'HolderDetails' in data['Design']['DesignDetails']:
                del data['Design']['DesignDetails']['HolderDetails']

            if 'CorrespondenceAddress' in data['Design']['DesignDetails']:
                del data['Design']['DesignDetails']['CorrespondenceAddress']

            if 'DesignSpecimenDetails' in data['Design']['DesignDetails']:
                del data['Design']['DesignDetails']['DesignSpecimenDetails']


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
            if 'RegistrationKind' in biblio_data and not limited_app.settings_dict.get('RegistrationKind', False):
                del biblio_data['RegistrationKind']
            if 'RegistrationKindCode' in biblio_data \
                    and not limited_app.settings_dict.get('RegistrationKindCode', False):
                del biblio_data['RegistrationKindCode']
            if 'RegistrationOfficeCode' in biblio_data \
                    and not limited_app.settings_dict.get('RegistrationOfficeCode', False):
                del biblio_data['RegistrationOfficeCode']
            if 'RepresentativeDetails' in biblio_data \
                    and not limited_app.settings_dict.get('RepresentativeDetails', False):
                del biblio_data['RepresentativeDetails']
            if 'Name' in biblio_data and not limited_app.settings_dict.get('Name', True):
                del biblio_data['Name']


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
            if 'RegistrationOfficeCode' in biblio_data \
                    and not limited_app.settings_dict.get('RegistrationOfficeCode', False):
                del biblio_data['RegistrationOfficeCode']
            if 'RepresentativeDetails' in biblio_data \
                    and not limited_app.settings_dict.get('RepresentativeDetails', False):
                del biblio_data['RepresentativeDetails']
