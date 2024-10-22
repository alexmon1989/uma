import os
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import List
from dataclasses import dataclass, field

from lxml import etree
from django.db.models import Prefetch
from django.conf import settings

from apps.search.models import IpcAppList, AppDocuments
from apps.search.services.services import application_get_app_elasticsearch_data


EXCEPTION_CODES: dict = {
    'N': 'Not used publication number',
}

DOCUMENT_KIND: dict = {
    'A': 'Specification for a patent for an invention granted without substantive examination. '
         'Specification for a declarative patent for an invention',
    'A1': 'Specification for a patent for an invention that was protected by the USSR author\'s certificate',
    'C1': 'Specification for a patent for an invention granted on the basis of a positive decision of '
          'the Patent Office of the former USSR',
    'C2': 'Specification for a patent for an invention granted on the ground of a national '
          'application. Specification for a patent for an invention granted on the graund of '
          'an application filed with the Patent Office of the former USSR for which no positive '
          'decision was taken',
    'U': 'Specification for a patent for a utility model. Specification for a declarative patent for '
         'a utility model',
}

DTD_FILE = os.path.join(settings.MEDIA_ROOT, 'st_37_dossier', 'ST37AuthorityFile_V2-2.dtd')


@dataclass
class DocumentId:
    country: str
    doc_number: str
    kind: str
    date: str | None = None


@dataclass
class PublicationReference:
    document_id: DocumentId


@dataclass
class ApplicationReference:
    country: str
    doc_number: str
    filing_date: str | None = None


@dataclass
class NotSearchableCode:
    code: str


@dataclass
class SearchableCode:
    searchable_language_code: List[str] | None = None
    not_searchable_code: NotSearchableCode = None


class SearchableDescriptionCode(SearchableCode):
    pass


class SearchableClaimsCode(SearchableCode):
    pass


class SearchableAbstractCode(SearchableCode):
    pass


@dataclass
class PriorityClaim:
    country: str
    doc_number: str
    date: str
    kind: str = ''
    sequence: str = ''
    priority_claim_kind: str = 'national'


@dataclass
class AuthorityFileEntry:
    publication_reference: PublicationReference
    searchable_description_code: SearchableDescriptionCode
    searchable_claims_code: SearchableClaimsCode
    searchable_abstract_code: SearchableAbstractCode
    application_reference: ApplicationReference | None = None
    priority_claims: List[PriorityClaim] | None = None
    exception_code: str | None = None


@dataclass
class Coverage:
    """Клас даних, що містить інформацію про типів патентних документів та виключень """
    document_kinds: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))
    exception_codes: defaultdict[str, int] = field(default_factory=lambda: defaultdict(int))


class St37CoverageCalculator:
    """Класс, що підраховує кількість типів патентних документів та виключень."""

    documents: List[AuthorityFileEntry]

    def __init__(self, documents: List[AuthorityFileEntry] = None):
        if not documents:
            self.documents = []
        else:
            self.documents = documents

    def calculate(self) -> Coverage:
        """Розраховує та повертає результати."""
        res = Coverage()
        for doc in self.documents:
            res.document_kinds[doc.publication_reference.document_id.kind] += 1
            if doc.exception_code:
                res.exception_codes[doc.exception_code] += 1

        return res


class St37DocumentsRepository:
    """Репозиторій для отримання патентних документів."""

    def get_documents(self) -> List[AuthorityFileEntry]:
        """Повертає список з патентними документами для досьє."""
        apps = IpcAppList.objects.filter(obj_type_id__in=[1, 2]).exclude(
            registration_date__isnull=True
        ).prefetch_related(
            Prefetch('appdocuments_set', queryset=AppDocuments.objects.filter(file_type='pdf'))
        ).order_by('pk')

        res = []
        for app in apps.iterator(chunk_size=1000):
            # Отримання даних з пошукового індексу (бібліографічні дані)
            biblio_data = application_get_app_elasticsearch_data(app.pk)['Patent']

            # Додання сформованої структури даних до результуючого списку
            res.append(self._get_authority_file_entry(app, biblio_data))

        return sorted(res, key=lambda x: (
            int(x.publication_reference.document_id.doc_number),
            x.publication_reference.document_id.kind,
            x.publication_reference.document_id.date,
        ))

    def _get_authority_file_entry(self, app: IpcAppList, biblio_data: dict) -> AuthorityFileEntry:
        """Формує структуру даних патенту, що готова для додання у відомче досьє."""
        document_id = DocumentId(
            country='UA',
            doc_number=str(biblio_data['I_11']),
            kind=biblio_data['I_13'],
            date=biblio_data['I_45.D'][-1].replace('-', '') if 'I_45.D' in biblio_data else None
        )
        publication_reference = PublicationReference(document_id=document_id)
        application_reference = ApplicationReference(
            doc_number=biblio_data['I_21'],
            country='UA',
            filing_date=biblio_data['I_43.D'][-1] if 'I_43.D' in biblio_data else None
        )

        docs = {
            'CL': [],
            'DE': [],
            'AB': []
        }
        mapping = {98: 'CL', 99: 'DE', 100: 'AB'}
        languages = {'UA': 'ua', 'EN': 'en', 'RU': 'ru'}
        for doc in app.appdocuments_set.all():
            file_name = doc.file_name.split('\\')[-1]
            key = mapping.get(doc.enter_num)
            if key:
                for lang_code, lang in languages.items():
                    if lang_code in file_name:
                        docs[key].append(lang)
                        break

        if docs['CL']:
            searchable_claims_code = SearchableClaimsCode(searchable_language_code=docs['CL'])
        else:
            searchable_claims_code = SearchableClaimsCode(not_searchable_code=NotSearchableCode(code='N'))

        if docs['DE']:
            searchable_description_code = SearchableDescriptionCode(searchable_language_code=list(set(docs['DE'])))
        else:
            searchable_description_code = SearchableDescriptionCode(not_searchable_code=NotSearchableCode(code='N'))

        if docs['AB']:
            searchable_abstract_code = SearchableAbstractCode(searchable_language_code=docs['AB'])
        else:
            searchable_abstract_code = SearchableAbstractCode(not_searchable_code=NotSearchableCode(code='N'))

        # Пріоритетні заявки
        priority_claims = []
        for priority_claim in biblio_data.get('I_30', []):
            if priority_claim.get('I_31') and priority_claim.get('I_32') and priority_claim.get('I_33'):
                priority_claims.append(
                    PriorityClaim(
                        country=priority_claim['I_33'],
                        doc_number=priority_claim['I_31'],
                        date=priority_claim['I_32'].replace('-', ''),
                    )
                )

        res = AuthorityFileEntry(
            publication_reference=publication_reference,
            application_reference=application_reference,
            searchable_claims_code=searchable_claims_code,
            searchable_description_code=searchable_description_code,
            searchable_abstract_code=searchable_abstract_code,
            priority_claims=priority_claims
        )
        return res


class St37FileCreator(ABC):
    """Абстрактний клас створення файлу з відомчим досьє."""
    documents: List[AuthorityFileEntry]
    coverage: Coverage

    def __init__(self, documents: List[AuthorityFileEntry] = None, coverage: Coverage = None):
        if not documents:
            self.documents = []
        else:
            self.documents = documents

        if coverage:
            self.coverage = coverage

    @abstractmethod
    def create_file(self) -> str:
        raise NotImplementedError


class St37XMLFileCreator(St37FileCreator):
    _root: etree.Element = None
    _authority_file_definition: etree.Element = None
    _date_produced: str = None

    def _create_root(self):
        """Створення кореневого елементу."""
        self._date_produced = datetime.now().strftime('%Y%m%d')

        self._root = etree.Element(
            'authority-file',
            {
                'country': 'UA',
                'date-produced': self._date_produced
            }
        )

    def _create_authority_file_definition(self):
        self._authority_file_definition = etree.SubElement(
            self._root,
            'authority-file-definition',
            {'grouped-af-indicator': "no", 'update-af-category': 'full'},
        )

    def _create_exception_codes_definition(self):
        """Створює вузли XML з інформацією про наявні коди виключень документів."""
        if self.coverage.exception_codes:
            exception_code_definitions = defaultdict(str)
            for e_c in self.coverage.exception_codes.items():
                if e_c[0] in EXCEPTION_CODES:
                    exception_code_definitions[e_c[0]] = EXCEPTION_CODES[e_c[0]]

            exception_code_list = etree.SubElement(
                self._authority_file_definition,
                'exception-code-list',
            )

            for e_c in exception_code_definitions.items():
                exception_code_definition_el = etree.SubElement(
                    exception_code_list,
                    'exception-code-definition',
                )
                exception_code = etree.SubElement(
                    exception_code_definition_el,
                    'exception-code',
                )
                exception_code.text = e_c[0]
                exception_code_description_el = etree.SubElement(
                    exception_code_definition_el,
                    'exception-code-description',
                )
                exception_code_description_el.text = e_c[1]

    def _create_document_kinds_definition(self):
        """Створює вузли XML з інформацією про наявні коди типів патентних документів."""
        document_kind_code_definitions = defaultdict(str)
        for d_k in self.coverage.document_kinds.items():
            if d_k[0] in DOCUMENT_KIND:
                document_kind_code_definitions[d_k[0]] = DOCUMENT_KIND[d_k[0]]

        document_kind_code_list_el = etree.SubElement(
            self._authority_file_definition,
            'document-kind-code-list',
        )

        for d_k in document_kind_code_definitions.items():
            document_kind_code_definition_el = etree.SubElement(
                document_kind_code_list_el,
                'document-kind-code-definition',
            )
            kind = etree.SubElement(
                document_kind_code_definition_el,
                'kind',
            )
            kind.text = d_k[0]
            document_kind_code_description = etree.SubElement(
                document_kind_code_definition_el,
                'document-kind-code-description',
            )
            document_kind_code_description.text = d_k[1]

    def _create_most_recent_document(self):
        etree.SubElement(
            self._authority_file_definition,
            'most-recent-document',
            {
                'publication-number': self.documents[-1].publication_reference.document_id.doc_number,
                'publication-date': self.documents[-1].publication_reference.document_id.date
            }
        )

    def _create_data_coverage(self):
        data_coverage = etree.SubElement(
            self._authority_file_definition,
            'data-coverage',
        )
        etree.SubElement(
            data_coverage,
            'publication-date-range',
            {
                'start-date': self.documents[0].publication_reference.document_id.date,
                'end-date': self.documents[-1].publication_reference.document_id.date
            }
        )
        etree.SubElement(
            data_coverage,
            'publication-number-range',
            {
                'begin-range-number': self.documents[0].publication_reference.document_id.doc_number,
                'end-range-number': self.documents[-1].publication_reference.document_id.doc_number
            }
        )
        kind_code_coverage = etree.SubElement(
            data_coverage,
            'kind-code-coverage',
        )
        for d_k in self.coverage.document_kinds.items():
            kind = etree.SubElement(
                kind_code_coverage,
                'kind',
            )
            kind.text = d_k[0]
            document_total_quantity = etree.SubElement(
                kind_code_coverage,
                'document-total-quantity',
            )
            document_total_quantity.text = str(d_k[1])

        exception_code_coverage = etree.SubElement(
            data_coverage,
            'exception-code-coverage',
        )
        for e_c in self.coverage.exception_codes.items():
            exception_code = etree.SubElement(
                exception_code_coverage,
                'exception-code',
            )
            exception_code.text = e_c[0]
            document_total_quantity = etree.SubElement(
                exception_code_coverage,
                'document-total-quantity',
            )
            document_total_quantity.text = str(e_c[1])

    def _create_authority_entries(self) -> None:
        for doc in self.documents:
            authority_file_entry = etree.SubElement(
                self._root,
                'authority-file-entry',
            )

            publication_reference = etree.SubElement(
                authority_file_entry,
                'publication-reference',
            )
            document_id = etree.SubElement(
                publication_reference,
                'document-id',
            )
            country = etree.SubElement(
                document_id,
                'country',
            )
            country.text = doc.publication_reference.document_id.country
            doc_number = etree.SubElement(
                document_id,
                'doc-number',
            )
            doc_number.text = doc.publication_reference.document_id.doc_number
            kind = etree.SubElement(
                document_id,
                'kind',
            )
            kind.text = doc.publication_reference.document_id.kind
            if doc.publication_reference.document_id.date:
                date = etree.SubElement(
                    document_id,
                    'date',
                )
                date.text = doc.publication_reference.document_id.date

            if doc.application_reference:
                application_reference = etree.SubElement(
                    authority_file_entry,
                    'application-reference',
                )
                country = etree.SubElement(
                    application_reference,
                    'country',
                )
                country.text = doc.application_reference.country
                doc_number = etree.SubElement(
                    application_reference,
                    'doc-number',
                )
                doc_number.text = doc.application_reference.doc_number
                if doc.application_reference.filing_date:
                    filing_date = etree.SubElement(
                        application_reference,
                        'filing-date',
                    )
                    filing_date.text = doc.application_reference.filing_date.replace('-', '')

            if doc.priority_claims:
                priority_claims = etree.SubElement(
                    authority_file_entry,
                    'priority-claims',
                )
                for item in doc.priority_claims:
                    priority_claim = etree.SubElement(
                        priority_claims,
                        'priority-claim',
                        {'sequence': item.sequence, 'priority-claim-kind': item.priority_claim_kind}
                    )
                    country = etree.SubElement(
                        priority_claim,
                        'country'
                    )
                    country.text = item.country
                    doc_number = etree.SubElement(
                        priority_claim,
                        'doc-number'
                    )
                    doc_number.text = item.doc_number
                    kind = etree.SubElement(
                        priority_claim,
                        'kind'
                    )
                    kind.text = item.kind
                    date = etree.SubElement(
                        priority_claim,
                        'date'
                    )
                    date.text = item.date

            # Опис
            searchable_description_code = etree.SubElement(
                authority_file_entry,
                'searchable-description-code',
            )
            if doc.searchable_description_code.not_searchable_code:
                etree.SubElement(
                    searchable_description_code,
                    'not-searchable-code',
                    {'code': doc.searchable_description_code.not_searchable_code.code}
                )
            else:
                for lang in doc.searchable_description_code.searchable_language_code:
                    searchable_language_code = etree.SubElement(
                        searchable_description_code,
                        'searchable-language-code'
                    )
                    searchable_language_code.text = lang

            # Реферат
            searchable_claims_code = etree.SubElement(
                authority_file_entry,
                'searchable-claims-code',
            )
            if doc.searchable_claims_code.not_searchable_code:
                etree.SubElement(
                    searchable_claims_code,
                    'not-searchable-code',
                    {'code': doc.searchable_claims_code.not_searchable_code.code}
                )
            else:
                for lang in doc.searchable_claims_code.searchable_language_code:
                    searchable_language_code = etree.SubElement(
                        searchable_claims_code,
                        'searchable-language-code'
                    )
                    searchable_language_code.text = lang

            # Формула
            searchable_abstract_code = etree.SubElement(
                authority_file_entry,
                'searchable-abstract-code',
            )
            if doc.searchable_abstract_code.not_searchable_code:
                etree.SubElement(
                    searchable_abstract_code,
                    'not-searchable-code',
                    {'code': doc.searchable_abstract_code.not_searchable_code.code}
                )
            else:
                for lang in doc.searchable_abstract_code.searchable_language_code:
                    searchable_language_code = etree.SubElement(
                        searchable_abstract_code,
                        'searchable-language-code'
                    )
                    searchable_language_code.text = lang

    def create_file(self) -> str:
        self._create_root()
        self._create_authority_file_definition()
        self._create_exception_codes_definition()
        self._create_document_kinds_definition()
        self._create_most_recent_document()
        self._create_data_coverage()
        self._create_authority_entries()

        tree = etree.ElementTree(self._root)
        # etree.indent(tree, space="\t", level=0)

        # Запис у файл
        file_name = f'UA_AF_{self._date_produced}.xml'
        file_path = os.path.join(settings.MEDIA_ROOT, 'st_37_dossier', file_name)
        with open(file_path, "wb") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\r'.encode('utf8'))
            f.write('<!DOCTYPE authority-file SYSTEM "ST37AuthorityFile_V2-2.dtd">\r'.encode('utf8'))
            tree.write(f, pretty_print=True, xml_declaration=False, encoding="UTF-8")

        return file_path


class St37FileValidator(ABC):
    file_path: str

    def __init__(self, file_path):
        self.file_path = file_path

    @abstractmethod
    def validate(self) -> None:
        raise NotImplementedError


class St37XMLFileValidator(St37FileValidator):

    def validate(self) -> None:

        with open(DTD_FILE) as f:
            dtd = etree.DTD(f)

        tree = etree.parse(self.file_path)

        if not dtd.validate(tree):
            error_msg = dtd.error_log.filter_from_errors()
            raise ValueError(f"DTD Validation failed: {error_msg}")


class St37DossierCreatorService:
    """Класс, що являє собою сервіс формування файлу відомчого досьє."""
    repository: St37DocumentsRepository
    coverage_calculator: St37CoverageCalculator
    file_creator: St37FileCreator
    file_validator: St37FileValidator | None = None

    def __init__(self,
                 repository: St37DocumentsRepository,
                 coverage_calculator: St37CoverageCalculator,
                 file_creator: St37FileCreator,
                 file_validator: St37FileValidator = None):
        self.repository = repository
        self.coverage_calculator = coverage_calculator
        self.file_creator = file_creator
        self.file_validator = file_validator

    def execute(self) -> str:
        # Отримання списку патентних документів
        documents = self.repository.get_documents()

        # Підрахунок кількості типів документів та виключень
        self.coverage_calculator.documents = documents
        coverage = self.coverage_calculator.calculate()

        # Створення файлу відомчого досьє
        self.file_creator.documents = documents
        self.file_creator.coverage = coverage
        file_path = self.file_creator.create_file()

        # Валідація створеного файлу
        if self.file_validator:
            self.file_validator.validate()

        return file_path
