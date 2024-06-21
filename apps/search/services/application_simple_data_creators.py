from abc import ABC, abstractmethod
from typing import List

from apps.search.models import IpcAppList


class ApplicationSimpleDataCreator(ABC):
    """Абстрактный класс для создания данных для простого поиска."""

    @abstractmethod
    def get_data(self, app: IpcAppList, data: dict) -> dict:
        pass


class ApplicationSimpleDataTMCreator(ApplicationSimpleDataCreator):
    """Создаёт данные ТМ для простого поиска."""

    def _get_obj_state(self, app: IpcAppList) -> int:
        return 2 if (app.registration_number and app.registration_number != '0') else 1

    def _get_app_number(self, data: dict) -> str | None:
        return data['TradeMark']['TrademarkDetails'].get('ApplicationNumber')

    def _get_app_date(self, app: IpcAppList, data: dict) -> str:
        if data['TradeMark']['TrademarkDetails'].get('ApplicationDate'):
            return data['TradeMark']['TrademarkDetails']['ApplicationDate']
        else:
            if app.app_date:
                return app.app_date.strftime('%Y-%m-%d')
            else:
                return app.app_input_date.strftime('%Y-%m-%d')

    def _get_protective_doc_number(self, data: dict) -> str | None:
        return data['TradeMark']['TrademarkDetails'].get('RegistrationNumber')

    def _get_rights_date(self, data: dict) -> str | None:
        return data['TradeMark']['TrademarkDetails'].get('RegistrationDate')

    def _get_applicants(self, data: dict) -> List[dict]:
        res = []
        if data['TradeMark']['TrademarkDetails'].get('ApplicantDetails'):
            for applicant in data['TradeMark']['TrademarkDetails']['ApplicantDetails']['Applicant']:
                res.append(
                    {
                        'name': applicant['ApplicantAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                            'FreeFormatNameDetails']['FreeFormatNameLine']
                    }
                )
                if 'FreeFormatNameLineOriginal' in applicant['ApplicantAddressBook'][
                    'FormattedNameAddress']['Name']['FreeFormatName']['FreeFormatNameDetails']:
                    res.append(
                        {
                            'name': applicant['ApplicantAddressBook']['FormattedNameAddress']['Name'][
                                'FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLineOriginal']
                        }
                    )
        return res

    def _get_owners(self, data: dict) -> List[dict]:
        res = []
        if data['TradeMark']['TrademarkDetails'].get('HolderDetails'):
            for holder in data['TradeMark']['TrademarkDetails']['HolderDetails']['Holder']:
                res.append(
                    {
                        'name': holder['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                            'FreeFormatNameDetails']['FreeFormatNameLine']
                    }
                )
                if 'FreeFormatNameLineOriginal' in holder['HolderAddressBook']['FormattedNameAddress']['Name'][
                    'FreeFormatName']['FreeFormatNameDetails']:
                    res.append(
                        {
                            'name': holder['HolderAddressBook']['FormattedNameAddress']['Name'][
                                'FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLineOriginal']
                        }
                    )
        return res

    def _get_title(self, data: dict) -> str:
        if data['TradeMark']['TrademarkDetails'].get('WordMarkSpecification'):
            return ', '.join(
                [x['#text'] for x in data['TradeMark']['TrademarkDetails']['WordMarkSpecification'][
                    'MarkSignificantVerbalElement']]
            )
        else:
            return ''

    def _get_registration_status_color(self, data: dict) -> str:
        status = data.get('TradeMark', {}).get('TrademarkDetails', {}).get('registration_status_color')

        if not status:
            status = 'green'

            red_transaction_types = [
                'TerminationNoRenewalFee',
                'TotalTerminationByOwner',
                'TotalInvalidationByCourt',
                'TotalTerminationByCourt',
                'TotalInvalidationByAppeal',
            ]

            if data.get('TradeMark', {}).get('Transactions'):
                last_transaction_type = data['TradeMark']['Transactions']['Transaction'][
                    len(data['TradeMark']['Transactions']['Transaction']) - 1].get('@type')

                if last_transaction_type in red_transaction_types:
                    status = 'red'

        return status

    def _get_agents(self, data) -> List[dict]:
        represents = []
        for represent in data['TradeMark']['TrademarkDetails'].get('RepresentativeDetails', {}).get('Representative', []):
            name = represent['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                'FreeFormatNameDetails']['FreeFormatNameDetails']['FreeFormatNameLine']
            address = represent['RepresentativeAddressBook']['FormattedNameAddress']['Address'][
                'FreeFormatAddress']['FreeFormatAddressLine']
            represents.append({'name': f"{name}, {address}"})
        return represents

    def get_data(self, app: IpcAppList, data: dict) -> dict:
        data = {
            'obj_state': self._get_obj_state(app),
            'app_number': self._get_app_number(data),
            'app_date': self._get_app_date(app, data),
            'protective_doc_number': self._get_protective_doc_number(data),
            'rights_date': self._get_rights_date(data),
            'applicant': self._get_applicants(data),
            'owner': self._get_owners(data),
            'title': self._get_title(data),
            'agent': self._get_agents(data)
        }

        return data


class ApplicationSimpleDataIDCreator(ApplicationSimpleDataCreator):
    """Создаёт данные ТМ для простого поиска."""

    def _get_obj_state(self, app: IpcAppList) -> int:
        return 2 if (app.registration_number and app.registration_number != '0') else 1

    def _get_app_number(self, data: dict) -> str | None:
        return data['Design']['DesignDetails'].get('DesignApplicationNumber')

    def _get_app_date(self, app: IpcAppList, data: dict) -> str:
        if data['Design']['DesignDetails'].get('DesignApplicationDate'):
            return data['Design']['DesignDetails']['DesignApplicationDate']
        else:
            if app.app_date:
                return app.app_date.strftime('%Y-%m-%d')
            else:
                return app.app_input_date.strftime('%Y-%m-%d')

    def _get_protective_doc_number(self, data: dict) -> str | None:
        return data['Design']['DesignDetails'].get('RegistrationNumber')

    def _get_rights_date(self, data: dict) -> str | None:
        return data['Design']['DesignDetails'].get('RecordEffectiveDate')

    def _get_applicants(self, data: dict) -> List[dict]:
        applicants = []
        if data['Design']['DesignDetails'].get('ApplicantDetails'):
            for applicant in data['Design']['DesignDetails']['ApplicantDetails']['Applicant']:
                applicants.append({'name': applicant['ApplicantAddressBook']['FormattedNameAddress']['Name'][
                    'FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLine']})
        return applicants

    def _get_owners(self, data: dict) -> List[dict]:
        owners = []
        if data['Design']['DesignDetails'].get('HolderDetails'):
            for x in data['Design']['DesignDetails']['HolderDetails']['Holder']:
                try:
                    owners.append({
                        'name': x['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                            'FreeFormatNameDetails']['FreeFormatNameLine']
                    })
                except KeyError:
                    pass
        return owners

    def _get_title(self, data: dict) -> str:
        return data['Design']['DesignDetails'].get('DesignTitle', '')

    def _get_registration_status_color(self, data: dict) -> str:
        status = data.get('Design', {}).get('DesignDetails', {}).get('registration_status_color')

        if not status:
            status = 'green'

            red_transaction_types = [
                'Termination',
                'TerminationByAppeal',
                'TerminationNoRenewalFee',
                'TotalInvalidationByAppeal',
                'TotalInvalidationByCourt',
                'TotalTerminationByOwner',
            ]

            if data.get('Design', {}).get('Transactions'):
                last_transaction_type = data['Design']['Transactions']['Transaction'][
                    len(data['Design']['Transactions']['Transaction']) - 1].get('@type')

                if last_transaction_type in red_transaction_types:
                    status = 'red'

        return status

    def _get_agents(self, data: dict) -> List[dict]:
        represents = []
        for represent in data['Design']['DesignDetails'].get('RepresentativeDetails', {}).get('Representative', []):
            name = represent['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                'FreeFormatNameDetails']['FreeFormatNameLine']
            address = represent['RepresentativeAddressBook']['FormattedNameAddress']['Address'][
                'FreeFormatAddress']['FreeFormatAddressLine']
            represents.append({'name': f"{name}, {address}"})
        return represents

    def _get_inventors(self, data: dict) -> List[dict]:
        inventors = []
        if data['Design']['DesignDetails'].get('DesignerDetails'):
            for inventor in data['Design']['DesignDetails']['DesignerDetails']['Designer']:
                inventors.append({'name': inventor['DesignerAddressBook']['FormattedNameAddress']['Name'][
                    'FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLine']})
        return inventors

    def get_data(self, app: IpcAppList, data: dict) -> dict:
        data = {
            'obj_state': self._get_obj_state(app),
            'app_number': self._get_app_number(data),
            'app_date': self._get_app_date(app, data),
            'protective_doc_number': self._get_protective_doc_number(data),
            'rights_date': self._get_rights_date(data),
            'applicant': self._get_applicants(data),
            'owner': self._get_owners(data),
            'title': self._get_title(data),
            'agent': self._get_agents(data),
            'inventor': self._get_inventors(data),
        }

        if data['obj_state'] == 2:
            data['registration_status_color'] = self._get_registration_status_color(data)

        return data
