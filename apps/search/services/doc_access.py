import unicodedata
from typing import Any

from django.contrib.auth.models import AnonymousUser, User


class UserDocAccessService:
    """Сервіс перевірки прав доступу користувача до документів заявки / охоронного документа."""

    _INV_UM_LD_EDRPOU_PATHS = (
        "Patent.I_71.EDRPOU",
        "Patent.I_73.EDRPOU",
        "Claim.I_71.EDRPOU",
        "Claim.I_73.EDRPOU",
    )
    _COPYRIGHT_EDRPOU_PATHS_PATHS = (
        "Certificate.CopyrightDetails.ApplicantDetails.Applicant.ApplicantAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        "Certificate.CopyrightDetails.EmployerDetails.Employer.EmployerAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        "Certificate.CopyrightDetails.AuthorDetails.Author.AuthorAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        "Certificate.CopyrightDetails.RepresentativeDetails.Representative.RepresentativeAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        "Certificate.CopyrightDetails.HolderDetails.Holder.HolderAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
    )
    _AGREEMENT_EDRPOU_PATHS_PATHS = (
        "Decision.DecisionDetails.ApplicantDetails.Applicant.ApplicantAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        "Decision.DecisionDetails.LicensorDetails.Licensor.LicensorAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        "Decision.DecisionDetails.LicenseeDetails.Licensee.LicenseeAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        "Decision.DecisionDetails.AuthorDetails.Author.AuthorAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
    )

    # Карта шляхів до кодів ЄДРПОУ залежно від типу об'єкта (idObjType)
    EDRPOU_PATHS: dict[int, tuple[str, ...]] = {
        1: _INV_UM_LD_EDRPOU_PATHS,
        2: _INV_UM_LD_EDRPOU_PATHS,
        3: _INV_UM_LD_EDRPOU_PATHS,
        4: (
            "TradeMark.TrademarkDetails.ApplicantDetails.Applicant.ApplicantAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
            "TradeMark.TrademarkDetails.HolderDetails.Holder.HolderAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        ),
        5: (
            "Geo.GeoDetails.ApplicantDetails.Applicant.ApplicantAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
            "Geo.GeoDetails.HolderDetails.Holder.HolderAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
        ),
        6: (
            "Design.DesignDetails.ApplicantDetails.Applicant.ApplicantAddressBook.FormattedNameAddress.Name.FreeFormatName.EDRPOU",
            "Design.DesignDetails.ApplicantDetails.Applicant.ApplicantAddressBook.FormattedNameAddress.Address.FormattedAddress.EDRPOU",
            "Design.DesignDetails.HolderDetails.Holder.HolderAddressBook.FormattedNameAddress.Address.FormattedAddress.EDRPOU",
        ),
        10: _COPYRIGHT_EDRPOU_PATHS_PATHS,
        13: _COPYRIGHT_EDRPOU_PATHS_PATHS,
        11: _AGREEMENT_EDRPOU_PATHS_PATHS,
        12: _AGREEMENT_EDRPOU_PATHS_PATHS,
    }

    # Шляхи до імен/найменувань осіб, які мають доступ до документів
    ALLOWED_PERSONS_PATHS: tuple[str, ...] = (
        "search_data.applicant.name",
        "search_data.inventor.name",
        "search_data.owner.name",
        "search_data.agent.name",
        # Адреса для листування (ТМ)
        "TradeMark.TrademarkDetails.CorrespondenceAddress.CorrespondenceAddressBook.Name.FreeFormatNameLine",
        # Адреса для листування (ПЗ)
        "Design.DesignDetails.CorrespondenceAddress.CorrespondenceAddressBook.FormattedNameAddress.Name.FreeFormatName.FreeFormatNameDetails.FreeFormatNameLine",
        # Адреса для листування (заявки на винаходи, корисні моделі)
        "Claim.I_98",
        # Адреса для листування (охоронні документи на винаходи, корисні моделі)
        "Patent.I_98",
    )

    # Таблиця нормалізації символів
    _NAME_TRANSLATION_TABLE = str.maketrans({
        # Латиниця -> Кирилиця
        "I": "І",
        "O": "О",
        "A": "А",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "K": "К",
        "M": "М",
        "P": "Р",
        "T": "Т",
        "X": "Х",
        "B": "В",
        # Дефіси, тире та розділові знаки -> пробіл
        "-": " ",
        "–": " ",
        "—": " ",
        "‑": " ",
        ".": " ",
        ",": " ",
        # Апострофи, лапки та невидимі спецсимволи -> видаляємо
        "'": None,
        "`": None,
        "’": None,
        "ʼ": None,
        "‘": None,
        '"': None,
        "«": None,
        "»": None,
        "„": None,
        "“": None,
        "”": None,
        "\xad": None,  # м'який перенос (soft hyphen)
        "\u200b": None,  # пробіл нульової ширини
        "\ufeff": None,  # BOM
    })

    def __init__(self, user: User | AnonymousUser, hit: dict[str, Any]) -> None:
        self.user = user
        self.hit = hit

    def has_access(self) -> bool:
        """Повертає ознаку доступності документа(ів) користувачу."""
        if self.user.is_anonymous:
            return False

        if self._check_vip():
            return True

        if self._check_nazk():
            return True

        # 1. Перевірка за ЄДРПОУ власника сертифіката
        if self._check_edrpou():
            return True

        # 2. Перевірка за ПІБ / найменуваннями (існуюча логіка)
        return self._check_names()

    def _check_vip(self) -> bool:
        return self.user.is_vip()

    def _check_nazk(self) -> bool:
        if "НАЗК" in self.user.groups.all().values_list("name", flat=True):
            from apps.search.utils import is_app_limited

            return not is_app_limited(self.hit)
        return False

    def _check_edrpou(self) -> bool:
        user_edrpou = self._get_user_edrpou()
        if not user_edrpou:
            return False

        doc_edrpou_codes = self._get_doc_edrpou_codes()
        return any(
            user_edrpou == code
            or (
                user_edrpou.isdigit()
                and code.isdigit()
                and int(user_edrpou) == int(code)
            )
            for code in doc_edrpou_codes
        )

    def _get_user_edrpou(self) -> str | None:
        if hasattr(self.user, "certificateowner") and self.user.certificateowner.pszSubjEDRPOUCode:
            return self.user.certificateowner.pszSubjEDRPOUCode.strip() or None
        return None

    def _get_doc_edrpou_codes(self) -> set[str]:
        id_obj_type = self.hit.get("Document", {}).get("idObjType")
        paths = self.EDRPOU_PATHS.get(id_obj_type, ())

        codes: set[str] = set()
        for path in paths:
            codes.update(self._extract_by_path(path))
        return codes

    def _check_names(self) -> bool:
        user_names = self._get_user_names()
        if not user_names:
            return False

        doc_persons = self._get_doc_persons()
        return any(
            user_name in person
            for person in doc_persons
            for user_name in user_names
        )

    def _get_user_names(self) -> list[str]:
        """Повертає список нормалізованих імен користувача (якщо роль - патентний повірений, перевіряється кілька імен)."""
        raw_names: list[str] = []
        if hasattr(self.user, "certificateowner"):
            if self.user.certificateowner.pszSubjFullName:
                raw_names.append(self.user.certificateowner.pszSubjFullName)
        elif self.user.is_patent_attorney():
            raw_names.append(f"{self.user.last_name} {self.user.first_name}")
            for patent_attorney in self.user.patentattorney_set.all():
                raw_names.append(patent_attorney.name)

        return [
            self._normalize_name(name)
            for name in raw_names
            if name and name.strip()
        ]

    def _get_doc_persons(self) -> list[str]:
        """Повертає список нормалізованих імен/найменувань осіб із документа."""
        persons: list[str] = []
        for path in self.ALLOWED_PERSONS_PATHS:
            persons.extend(self._extract_by_path(path))
        return [self._normalize_name(person) for person in persons]

    def _normalize_name(self, name: str) -> str:
        """Нормалізує ім'я: Unicode NFKC, верхній регістр, гомогліфи, розділові знаки, апострофи/лапки та пробіли."""
        normalized = unicodedata.normalize("NFKC", name).upper()
        normalized = normalized.translate(self._NAME_TRANSLATION_TABLE)
        return " ".join(normalized.split())

    def _extract_by_path(self, path: str) -> list[str]:
        """Витягує значення з self.hit за шляхом виду 'A.B.C', автоматично розгортаючи списки."""
        current: list[Any] = [self.hit]
        for key in path.split("."):
            next_items: list[Any] = []
            for item in current:
                if isinstance(item, dict) and key in item:
                    val = item[key]
                    if isinstance(val, list):
                        next_items.extend(val)
                    elif val is not None:
                        next_items.append(val)
            current = next_items
            if not current:
                break

        return [
            str(v).strip()
            for v in current
            if not isinstance(v, (dict, list)) and str(v).strip()
        ]
