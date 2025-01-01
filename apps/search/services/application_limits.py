import json
from abc import ABC, abstractmethod

from apps.search.models import AppLimited


class LimitsMucToDictConverter(ABC):
    """Інтерфейс конвертора налаштувань обмежень з MUC у dict.

    :cvar muc_limits set: Набір обмежень MUC.
    """
    muc_limits: set

    def __init__(self, muc_limits: set | None = None):
        if muc_limits is None:
            muc_limits = set()
        self.muc_limits = muc_limits

    @abstractmethod
    def convert(self) -> dict:
        """
        :return: dict з інформацією про обмеження.
        :rtype: dict
        """
        pass


class LimitsMucToDictConverterInvUMLD(LimitsMucToDictConverter):
    """Реалізація конвертора налаштувань обмежень з MUC у dict для винаходів, КМ, топографій."""
    def convert(self) -> dict:
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

        return res


class LimitsMucToDictConverterID(LimitsMucToDictConverter):
    """Реалізація конвертора налаштувань обмежень з MUC у dict для промислових зразків."""
    def convert(self) -> dict:
        res = {
            'DesignSpecimenDetails': 40 not in self.muc_limits,
            'ApplicantDetails': 41 not in self.muc_limits,
            'DesignerDetails': 42 not in self.muc_limits,
            'HolderDetails': 43 not in self.muc_limits,
            'CorrespondenceAddress': 44 not in self.muc_limits,
            'DesignTitle': 45 not in self.muc_limits,
            'RepresentativeDetails': 46 not in self.muc_limits,
        }

        return res


class LimitsMucToDictConverterCR(LimitsMucToDictConverter):
    """Реалізація конвертора налаштувань обмежень з MUC у dict для авторського права."""
    def convert(self) -> dict:
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

        return res


class LimitsMucToDictConverterDecision(LimitsMucToDictConverter):
    """Реалізація конвертора налаштувань обмежень з MUC у dict для договорів авторського права."""
    def convert(self) -> dict:
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

        return res


# Конвертери з MUC у dict
MUC_TO_DICT_CONVERTERS = {
    1: LimitsMucToDictConverterInvUMLD,
    2: LimitsMucToDictConverterInvUMLD,
    3: LimitsMucToDictConverterInvUMLD,
    6: LimitsMucToDictConverterID,
    10: LimitsMucToDictConverterCR,
    11: LimitsMucToDictConverterDecision,
    12: LimitsMucToDictConverterDecision,
    13: LimitsMucToDictConverterCR,
}


# Статуси обмежень
LIMITS_STATUS = {
    'SET': 922,  # Встановлено обмеження
    'REMOVED': 923,  # Знято обмеження
    'NONE': 924  # Відсутні обмеження
}


class LimitsService:
    """Клас сервісу, що обмежує дані ОПВ (фактично записує у БД дані щодо обмежень).

    :cvar app_number str: Номер заявки.
    :cvar obj_type_id int: Тип об'єкта.
    :cvar limits_status int: Статус обмежень.
    :cvar limits dict: Перелік обмежень.
    :cvar app_limited AppLimited: Модель обмеженої заявки
    """
    app_number: str
    obj_type_id: int
    limits_status: int
    muc_limits: set
    app_limited: AppLimited = None

    def __init__(self,
                 app_number: str,
                 obj_type_id: int,
                 limits_status: int,
                 limits: dict):
        self.app_number = app_number
        self.obj_type_id = obj_type_id
        self.limits_status = limits_status
        self.limits = limits

    def _handle_no_limits(self) -> bool:
        if self.app_limited:
            self.app_limited.delete()
            return True
        return False

    def _handle_limits(self) -> bool:
        if not self.app_limited:
            # Якщо запис відсутній, то відбувається його створення
            return self._create_new_record()
        else:
            # Якщо запис наявний, то необхідно оновити його
            return self._update_existing_record()

    def _create_new_record(self) -> bool:
        """Створює новий запис обмеженої заявки."""
        AppLimited.objects.create(
            app_number=self.app_number,
            obj_type_id=self.obj_type_id,
            settings_json=json.dumps(self.limits, indent=4),
            cancelled=self.limits_status == LIMITS_STATUS['REMOVED']
        )
        return True

    def _update_existing_record(self) -> bool:
        """Оновлює запис обмеженої заявки."""
        need_update = False

        limits_json = json.dumps(self.limits, indent=4)
        if self.app_limited.settings_json != limits_json:
            self.app_limited.settings_json = limits_json
            need_update = True

        cancelled = self.limits_status == LIMITS_STATUS['REMOVED']
        if self.app_limited.cancelled != cancelled:
            self.app_limited.cancelled = cancelled
            need_update = True

        if need_update:
            self.app_limited.save()
            return True

        return False

    def process(self) -> bool:
        # Отримання даних про обмеження з БД UMA
        self.app_limited = AppLimited.objects.filter(
            app_number=self.app_number,
            obj_type_id=self.obj_type_id
        ).first()

        if self.limits_status == LIMITS_STATUS['NONE']:
            return self._handle_no_limits()
        else:
            return self._handle_limits()
