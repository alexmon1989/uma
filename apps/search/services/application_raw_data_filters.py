from abc import ABC, abstractmethod


class ApplicationRawDataFilter(ABC):
    """Абстрактный класс фильтра сырых данных."""

    @abstractmethod
    def filter_data(self, data: dict) -> None:
        pass


class ApplicationRawDataTMLimitedFilter(ApplicationRawDataFilter):
    """Фильтрует сырые данные ТМ в случае если она является ограниченной для публикации.."""

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
