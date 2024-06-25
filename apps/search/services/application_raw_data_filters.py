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
