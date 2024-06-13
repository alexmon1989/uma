from abc import ABC, abstractmethod
import datetime


class ApplicationIndexationValidator(ABC):
    _app_data: dict

    def __init__(self, app_data: dict):
        self._app_data = app_data

    @abstractmethod
    def validate(self) -> bool:
        pass


class ApplicationIndexationTMValidator(ApplicationIndexationValidator):
    """Валидатор для ТМ."""

    def _validate_publication_date(self) -> None:
        today = datetime.datetime.now()

        publication = self._app_data.get('TradeMark', {}).get('TrademarkDetails', {}).get('PublicationDetails', [])
        for item in publication:
            if datetime.datetime.strptime(item['PublicationDate'], '%Y-%m-%d') > today:
                raise ValueError("Publication date cannot be in future time")

    def _validate_transaction_date(self) -> None:
        today = datetime.datetime.now()

        transactions = self._app_data.get('TradeMark', {}).get('Transactions', {}).get('Transaction', [])
        for item in transactions:
            if datetime.datetime.strptime(item['@bulletinDate'], '%Y-%m-%d') > today:
                raise ValueError("Publication date cannot be in future time")

    def validate(self):
        self._validate_publication_date()
        self._validate_transaction_date()
