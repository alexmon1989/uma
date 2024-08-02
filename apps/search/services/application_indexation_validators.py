from abc import ABC, abstractmethod
import datetime


class ApplicationIndexationValidator(ABC):
    _app_data: dict

    def __init__(self, app_data: dict):
        self._app_data = app_data

    @abstractmethod
    def validate(self) -> None:
        pass


class ApplicationIndexationTMValidator(ApplicationIndexationValidator):
    """Валидатор для ТМ."""

    def _validate_publication_date(self) -> None:
        today = datetime.datetime.now()

        publication = self._app_data.get('TradeMark', {}).get('TrademarkDetails', {}).get('PublicationDetails', [])
        for item in publication:
            if datetime.datetime.strptime(item['PublicationDate'], '%Y-%m-%d') > today:
                raise ValueError(f"Publication date cannot be in future time "
                                 f"{self._app_data['TradeMark']['TrademarkDetails']['ApplicationNumber']}")

    def _validate_transaction_date(self) -> None:
        today = datetime.datetime.now()

        transactions = self._app_data.get('TradeMark', {}).get('Transactions', {}).get('Transaction', [])
        for item in transactions:
            if datetime.datetime.strptime(item['@bulletinDate'], '%Y-%m-%d') > today:
                raise ValueError(f"Transaction date cannot be in future time: "
                                 f"{self._app_data['TradeMark']['TrademarkDetails']['ApplicationNumber']}")

    def validate(self):
        self._validate_publication_date()
        self._validate_transaction_date()


class ApplicationIndexationIDValidator(ApplicationIndexationValidator):
    def _validate_publication_date(self) -> None:
        today = datetime.datetime.now()

        publication = self._app_data.get('Design', {}).get('DesignDetails', {}).get('RecordPublicationDetails', [])
        for item in publication:
            if datetime.datetime.strptime(item['PublicationDate'], '%Y-%m-%d') > today:
                raise ValueError(f"Publication date cannot be in future time: "
                                 f"{self._app_data['Design']['DesignDetails']['DesignApplicationNumber']}")

    def _validate_transaction_date(self) -> None:
        today = datetime.datetime.now()

        transactions = self._app_data.get('Design', {}).get('Transactions', {}).get('Transaction', [])
        for item in transactions:
            if datetime.datetime.strptime(item['@bulletinDate'], '%Y-%m-%d') > today:
                raise ValueError(f"Transaction date cannot be in future time: "
                                 f"{self._app_data['Design']['DesignDetails']['DesignApplicationNumber']}")

    def validate(self) -> None:
        self._validate_publication_date()
        self._validate_transaction_date()


class ApplicationIndexationInvUMLDValidator(ApplicationIndexationValidator):

    def _validate_i_43_claim(self) -> None:
        """Проверяет может ли заявка на изобретение быть добавлена в поисковый индекс."""
        today = datetime.datetime.now()

        i_43 = self._app_data.get('Claim', {}).get('I_43.D', [])
        for item in i_43:
            if datetime.datetime.strptime(item, '%Y-%m-%d') > today:
                raise ValueError(f"Publication date cannot be in future time: {self._app_data['Claim']['I_21']}")

    def validate(self) -> None:
        self._validate_i_43_claim()
