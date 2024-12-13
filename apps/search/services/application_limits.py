import json
from abc import ABC, abstractmethod

from apps.search.models import AppLimited


class LimitsMucToJSONConverter(ABC):
    """Інтерфейс конвертора налаштувань обмежень з MUC у JSON."""
    muc_limits: set

    def __init__(self, muc_limits: set | None = None):
        if muc_limits is None:
            muc_limits = set()
        self.muc_limits = muc_limits

    @abstractmethod
    def convert(self) -> str:
        pass


class LimitsMucToJSONConverterInvUMLD(LimitsMucToJSONConverter):
    """Реалізація конвертора налаштувань обмежень з MUC у JSON для винаходів, КМ, топографій."""
    def convert(self) -> str:
        res = {
            'I_71': 1 not in self.muc_limits,
            'I_72': 2 not in self.muc_limits,
            'I_73': 3 not in self.muc_limits,
            'I_98': 4 not in self.muc_limits,
            'I_98_Index': 4 not in self.muc_limits,
            'CL': 5 not in self.muc_limits,
            'DE': 6 not in self.muc_limits,
            'AB': 7 not in self.muc_limits,
            'I_54': 9 not in self.muc_limits,
            'I_56': 10 not in self.muc_limits,
            'I_74': 11 not in self.muc_limits,
        }

        return json.dumps(res, indent=4)


class LimitsMucToJSONConverterID(LimitsMucToJSONConverter):
    """Реалізація конвертора налаштувань обмежень з MUC у JSON для промислових зразків."""
    def convert(self) -> str:
        res = {
            'DesignSpecimenDetails': 40 not in self.muc_limits,
            'ApplicantDetails': 41 not in self.muc_limits,
            'DesignerDetails': 42 not in self.muc_limits,
            'HolderDetails': 43 not in self.muc_limits,
            'CorrespondenceAddress': 44 not in self.muc_limits,
            'DesignTitle': 45 not in self.muc_limits,
            'RepresentativeDetails': 46 not in self.muc_limits,
        }

        return json.dumps(res, indent=4)


class LimitsMucToJSONConverterCR(LimitsMucToJSONConverter):
    """Реалізація конвертора налаштувань обмежень з MUC у JSON для авторського права."""
    def convert(self) -> str:
        res = {
            'AuthorDetails': 12 not in self.muc_limits,
            'ApplicantDetails': 12 not in self.muc_limits,
            'PromulgationData': 13 not in self.muc_limits,
            'Annotation': 14 not in self.muc_limits,
            'HolderDetails': 15 not in self.muc_limits,
            'EmployerDetails': 15 not in self.muc_limits,
            'RepresentativeDetails': 16 not in self.muc_limits,
            'Name': 17 not in self.muc_limits,
            'NameShort': 17 not in self.muc_limits,
        }

        return json.dumps(res, indent=4)


class LimitsMucToJSONConverterDecision(LimitsMucToJSONConverter):
    """Реалізація конвертора налаштувань обмежень з MUC у JSON для договорів авторського права."""
    def convert(self) -> str:
        res = {
            'LicenseeDetails': 18 not in self.muc_limits,
            'LicensorDetails': 18 not in self.muc_limits,
            'RegistrationKind': 22 not in self.muc_limits,
            'RegistrationKindCode': 22 not in self.muc_limits,
            'AuthorDetails': 35 not in self.muc_limits,
            'ApplicantDetails': 35 not in self.muc_limits,
            'Annotation': 37 not in self.muc_limits,
            'Name': 38 not in self.muc_limits,
            'NameShort': 38 not in self.muc_limits,
            'RepresentativeDetails': 39 not in self.muc_limits,
        }

        return json.dumps(res, indent=4)


MUC_TO_JSON_CONVERTERS = {
    1: LimitsMucToJSONConverterInvUMLD,
    2: LimitsMucToJSONConverterInvUMLD,
    3: LimitsMucToJSONConverterInvUMLD,
    6: LimitsMucToJSONConverterID,
    10: LimitsMucToJSONConverterCR,
    11: LimitsMucToJSONConverterDecision,
    12: LimitsMucToJSONConverterDecision,
    13: LimitsMucToJSONConverterCR,
}


class LimitsService:
    """Клас сервісу, що обмежує дані ОПВ на основі даних з ЦЕАД (MUC)."""
    app_number: str  # номер заявки
    obj_type_id: int  # тип об'єкта
    limits_status: int  # статус обмежень
    muc_limits: set  # перелік обмежень (MUC)
    muc_to_json_converter: LimitsMucToJSONConverter  # конвертер MUC у JSON

    def __init__(self,
                 app_number: str,
                 obj_type_id: int,
                 limits_status: int,
                 muc_limits: set,
                 muc_to_json_converter: LimitsMucToJSONConverter):
        self.app_number = app_number
        self.obj_type_id = obj_type_id
        self.limits_status = limits_status
        self.muc_limits = muc_limits
        self.muc_to_json_converter = muc_to_json_converter

    def process(self) -> bool:
        # Отримання даних про обмеження з БД UMA
        app_limited = AppLimited.objects.filter(
            app_number=self.app_number,
            obj_type_id=self.obj_type_id
        ).first()

        # Обробка статусів: 922 - встановлено обмеження, 923 - знято обмеження, 924 - відсутні обмеження
        if self.limits_status == 924:
            if app_limited:
                app_limited.delete()
        else:
            self.muc_to_json_converter.muc_limits = self.muc_limits
            limits_json = self.muc_to_json_converter.convert()

            if not app_limited:
                # Якщо запис відсутній, то відбуваєтсья його створення
                AppLimited.objects.create(
                    app_number=self.app_number,
                    obj_type_id=self.obj_type_id,
                    settings_json=limits_json,
                    cancelled=self.limits_status == 923
                )
                return True
            else:
                # Якщо запис наявний, то необхідно оновити його
                need_update = False

                if app_limited.settings_json != limits_json:
                    app_limited.settings_json = limits_json
                    need_update = True

                cancelled = self.limits_status == 923
                if app_limited.cancelled != cancelled:
                    app_limited.cancelled = cancelled
                    need_update = True

                if need_update:
                    app_limited.save()
                    return True
            return False
