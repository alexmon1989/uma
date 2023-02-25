from apps.search.dataclasses import InidCode

from typing import List
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches
from docx.text.paragraph import Paragraph

from django.conf import settings


class ReportItem(ABC):
    """Интерфейс объекта пром. собств., который попадает в отчёт."""
    application_data: dict
    ipc_fields: List[InidCode]  # Список полей для отображения с флагом доступно ли поле для отображения

    def _get_inid(self, obj_type_id: int, code: str, obj_state: int = 1) -> InidCode | None:
        """Возвращает признак необходимости отображения поля."""
        try:
            return next(
                filter(
                    lambda x: x.obj_type_id == obj_type_id and x.code == code and x.obj_state == obj_state,
                    self.ipc_fields
                )
            )
        except StopIteration:
            return None


class ReportItemDocx(ReportItem):

    @abstractmethod
    def write(self, document: Document) -> Paragraph:
        """Возвращает абзац текста с информацией об объекте пром. собств."""
        raise NotImplemented

    def __init__(self, application_data: dict, ipc_fields: List[InidCode]):
        self.application_data = application_data
        self.ipc_fields = ipc_fields


class ReportItemDocxTM(ReportItemDocx):
    """Торговая марка."""
    _paragraph: Paragraph
    document: Document
    obj_type_id = 4

    def _write_540(self) -> None:
        """Добавляет изображение в документ."""
        inid = self._get_inid(self.obj_type_id, '540', self.application_data['search_data']['obj_state'])
        mark_image_filename = self.application_data['TradeMark']['TrademarkDetails'].get(
            'MarkImageDetails', {}
        ).get(
            'MarkImage', {}
        ).get(
            'MarkImageFilename'
        )
        if inid and inid.visible and mark_image_filename:
            path = Path(self.application_data['Document']['filesPath'].replace('\\', '/'))
            parts_len = len(path.parts)
            # Путь к изображению на диске
            mark_image_filepath = Path(settings.MEDIA_ROOT) / path.parts[parts_len - 3]
            mark_image_filepath /= mark_image_filepath / path.parts[parts_len - 2]
            mark_image_filepath /= path.parts[parts_len - 1]
            mark_image_filepath /= mark_image_filename
            run = self._paragraph.add_run()
            run.add_picture(str(mark_image_filepath), width=Inches(2.5))
            self._paragraph.add_run('\r')

    def _write_111(self) -> None:
        """Записывает номер свидетельства в документ."""
        inid = self._get_inid(self.obj_type_id, '111', self.application_data['search_data']['obj_state'])
        registration_number = self.application_data['TradeMark']['TrademarkDetails'].get('RegistrationNumber')
        if inid and inid.visible and registration_number:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(registration_number).bold = True
            self._paragraph.add_run('\r')

    def _write_141(self) -> None:
        """Записывает в документ данные об ИНИД (141) Дата закінчення строку дії реєстрації знака."""
        inid = self._get_inid(self.obj_type_id, '141', self.application_data['search_data']['obj_state'])
        termination_date = self.application_data['TradeMark']['TrademarkDetails'].get('TerminationDate')
        if inid and inid.visible and termination_date:
            termination_date = datetime.strptime(termination_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(termination_date).bold = True
            self._paragraph.add_run('\r')

    def _write_151(self) -> None:
        """Записывает в документ данные об ИНИД (151) Дата реєстрації."""
        inid = self._get_inid(self.obj_type_id, '151', self.application_data['search_data']['obj_state'])
        registration_date = self.application_data['TradeMark']['TrademarkDetails'].get('RegistrationDate')
        if inid and inid.visible and registration_date:
            registration_date = datetime.strptime(registration_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(registration_date).bold = True
            self._paragraph.add_run('\r')

    def _write_181(self) -> None:
        """Записывает в документ данные об ИНИД (181) Очікувана дата закінчення строку дії реєстрації."""
        inid = self._get_inid(self.obj_type_id, '181', self.application_data['search_data']['obj_state'])
        expiry_date = self.application_data['TradeMark']['TrademarkDetails'].get('ExpiryDate')
        if inid and inid.visible and expiry_date:
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(expiry_date).bold = True
            self._paragraph.add_run('\r')

    def _write_186(self) -> None:
        """Записывает в документ данные об ИНИД (186) Очікувана дата продовження строку дії реєстрації."""
        inid = self._get_inid(self.obj_type_id, '186', self.application_data['search_data']['obj_state'])
        prolongation_expiry_date = self.application_data['TradeMark']['TrademarkDetails'].get('ProlonagationExpiryDate')
        if inid and inid.visible and prolongation_expiry_date:
            prolongation_expiry_date = datetime.strptime(prolongation_expiry_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(prolongation_expiry_date).bold = True
            self._paragraph.add_run('\r')

    def _write_210(self) -> None:
        """Записывает в документ данные об ИНИД (210) Порядковий номер заявки."""
        inid = self._get_inid(self.obj_type_id, '210', self.application_data['search_data']['obj_state'])
        app_number = self.application_data['TradeMark']['TrademarkDetails'].get('ApplicationNumber')
        if inid and inid.visible and app_number:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(app_number).bold = True
            self._paragraph.add_run('\r')

    def _write_220(self) -> None:
        """Записывает в документ данные об ИНИД (220) Дата подання заявки."""
        inid = self._get_inid(self.obj_type_id, '220', self.application_data['search_data']['obj_state'])
        app_date = self.application_data['TradeMark']['TrademarkDetails'].get('ApplicationDate')
        if inid and inid.visible and app_date:
            app_date = datetime.strptime(app_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(app_date).bold = True
            self._paragraph.add_run('\r')

    def _write_531(self) -> None:
        """Записывает в документ данные об ИНИД (531) Віденська класифікація."""
        inid = self._get_inid(self.obj_type_id, '531', self.application_data['search_data']['obj_state'])
        vienna_classes = self.application_data['TradeMark']['TrademarkDetails'].get(
            'MarkImageDetails', {}
        ).get(
            'MarkImage', {}
        ).get(
            'MarkImageCategory', {}
        ).get(
            'CategoryCodeDetails', {}
        ).get(
            'CategoryCode'
        )
        if inid and inid.visible and vienna_classes:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            for vienna_class in vienna_classes:
                self._paragraph.add_run(f"\r{vienna_class}").bold = True
            self._paragraph.add_run('\r')

    def _write_300(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (300) Дані щодо пріоритету відповідно до Паризької конвенції та інші дані,
        пов'язані зі старшинством або реєстрацією знака у країні походження.
        TODO: Добавить приоритет по классам.
        """
        inid = self._get_inid(self.obj_type_id, '300', self.application_data['search_data']['obj_state'])
        priority = self.application_data['TradeMark']['TrademarkDetails'].get(
            'PriorityDetails', {}
        ).get(
            'Priority'
        )
        if inid and inid.visible and priority:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            for item in priority:
                self._paragraph.add_run('\r')
                if 'PriorityNumber' in item:
                    self._paragraph.add_run(f"{item['PriorityNumber']}; ").bold = True
                if 'PriorityDate' in item:
                    self._paragraph.add_run(f"{item['PriorityDate']}; ").bold = True
                if 'PriorityCountryCode' in item:
                    self._paragraph.add_run(f"{item['PriorityCountryCode']}").bold = True
            self._paragraph.add_run('\r')

    def _write_731(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (731) Ім'я та адреса заявника
        """
        inid = self._get_inid(self.obj_type_id, '731', self.application_data['search_data']['obj_state'])
        applicants = self.application_data['TradeMark']['TrademarkDetails'].get(
            'ApplicantDetails', {}
        ).get(
            'Applicant'
        )
        if inid and inid.visible and applicants:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            for applicant in applicants:
                self._paragraph.add_run('\r')
                try:
                    self._paragraph.add_run(
                        applicant['ApplicantAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                            'FreeFormatNameDetails']['FreeFormatNameLine']
                    ).bold = True
                except KeyError:
                    pass

                if self.application_data['search_data']['obj_state'] == 2:
                    self._paragraph.add_run('\r')
                    try:
                        self._paragraph.add_run(
                            applicant['ApplicantAddressBook']['FormattedNameAddress']['Address']['FreeFormatAddress'][
                                'FreeFormatAddressLine']
                        )
                    except KeyError:
                        pass

                    try:
                        country = applicant['ApplicantAddressBook']['FormattedNameAddress']['Address'][
                            'AddressCountryCode']
                        self._paragraph.add_run(
                            f" ({country})"
                        )
                    except KeyError:
                        pass
            self._paragraph.add_run('\r')

    def _write_732(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (732) Ім'я та адреса володільця реєстрації
        """
        inid = self._get_inid(self.obj_type_id, '732', self.application_data['search_data']['obj_state'])
        holders = self.application_data['TradeMark']['TrademarkDetails'].get(
            'HolderDetails', {}
        ).get(
            'Holder'
        )
        if inid and inid.visible and holders:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            for holder in holders:
                self._paragraph.add_run('\r')
                try:
                    self._paragraph.add_run(
                        holder['HolderAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                            'FreeFormatNameDetails']['FreeFormatNameLine']
                    ).bold = True
                except KeyError:
                    pass

                self._paragraph.add_run('\r')
                try:
                    self._paragraph.add_run(
                        holder['HolderAddressBook']['FormattedNameAddress']['Address']['FreeFormatAddress'][
                            'FreeFormatAddressLine']
                    )
                except KeyError:
                    pass

                try:
                    country = holder['HolderAddressBook']['FormattedNameAddress']['Address']['AddressCountryCode']
                    self._paragraph.add_run(
                        f" ({country})"
                    )
                except KeyError:
                    pass
            self._paragraph.add_run('\r')

    def _write_740(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (740) Ім'я та адреса володільця реєстрації
        """
        inid = self._get_inid(self.obj_type_id, '740', self.application_data['search_data']['obj_state'])
        representatives = self.application_data['TradeMark']['TrademarkDetails'].get(
            'RepresentativeDetails', {}
        ).get(
            'Representative'
        )
        if inid and inid.visible and representatives:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            for representative in representatives:
                self._paragraph.add_run('\r')
                try:
                    self._paragraph.add_run(
                        representative['RepresentativeAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                            'FreeFormatNameDetails']['FreeFormatNameDetails']['FreeFormatNameLine']
                    ).bold = True
                except KeyError:
                    pass

                self._paragraph.add_run('\r')
                try:
                    self._paragraph.add_run(
                        representative['RepresentativeAddressBook']['FormattedNameAddress']['Address'][
                            'FreeFormatAddress']['FreeFormatAddressLine']
                    )
                except KeyError:
                    pass

                try:
                    country = representative['RepresentativeAddressBook']['FormattedNameAddress']['Address'][
                        'AddressCountryCode']
                    self._paragraph.add_run(
                        f" ({country})"
                    )
                except KeyError:
                    pass
            self._paragraph.add_run('\r')

    def _write_750(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (750) Адреса для листування
        """
        inid = self._get_inid(self.obj_type_id, '750', self.application_data['search_data']['obj_state'])
        correspondence = self.application_data['TradeMark']['TrademarkDetails'].get(
            'CorrespondenceAddress', {}
        ).get(
            'CorrespondenceAddressBook'
        )
        if inid and inid.visible and correspondence:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            self._paragraph.add_run('\r')
            try:
                self._paragraph.add_run(
                    correspondence['Name']['FreeFormatNameLine']
                ).bold = True
            except KeyError:
                pass

            self._paragraph.add_run('\r')
            try:
                self._paragraph.add_run(
                    correspondence['Address']['FreeFormatAddressLine']
                )
            except KeyError:
                pass

            try:
                country = correspondence['Address']['AddressCountryCode']
                self._paragraph.add_run(
                    f" ({country})"
                )
            except KeyError:
                pass
        self._paragraph.add_run('\r')

    def _write_591(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (591) Інформація щодо заявлених кольорів
        """
        inid = self._get_inid(self.obj_type_id, '591', self.application_data['search_data']['obj_state'])
        colors = self.application_data['TradeMark']['TrademarkDetails'].get(
            'MarkImageDetails', {}
        ).get(
            'MarkImage', {}
        ).get(
            'MarkImageColourClaimedText'
        )
        if inid and inid.visible and colors:
            self._paragraph.add_run(f"({inid.code})").bold = True
            colors_str = ', '.join([x['#text'] for x in colors])
            self._paragraph.add_run(f"\t{inid.title}: {colors_str}")
            self._paragraph.add_run('\r')

    def _write_511(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (511) Індекси Ніццької класифікації
        """
        inid = self._get_inid(self.obj_type_id, '511', self.application_data['search_data']['obj_state'])
        goods = self.application_data['TradeMark']['TrademarkDetails'].get(
            'GoodsServicesDetails', {}
        ).get(
            'GoodsServices', {}
        ).get(
            'ClassDescriptionDetails', {}
        ).get(
            'ClassDescription'
        )
        if inid and inid.visible and goods:
            self._paragraph.add_run(f"({inid.code})").bold = True
            goods_classes_str = ', '.join([str(x['ClassNumber']) for x in goods])
            self._paragraph.add_run(f"\t{inid.title}: {goods_classes_str}")
            for item in goods:
                self._paragraph.add_run('\r')
                self._paragraph.add_run(f"Кл. {item['ClassNumber']}:\t").bold = True
                terms = item['ClassificationTermDetails']['ClassificationTerm']
                values_str = '; '.join([x['ClassificationTermText'] for x in terms])
                self._paragraph.add_run(values_str)
            self._paragraph.add_run('\r')

    def write(self, document: Document) -> Paragraph:
        """Записывает информацию о ТМ в абзац и возвращает его."""
        self.document = document
        self._paragraph = self.document.add_paragraph('')

        self._write_540()
        self._write_111()
        self._write_151()
        self._write_141()
        self._write_181()
        self._write_186()
        self._write_210()
        self._write_220()
        self._write_531()
        self._write_300()
        self._write_731()
        self._write_732()
        self._write_740()
        self._write_750()
        self._write_591()
        self._write_511()

        return self._paragraph


class ReportWriter(ABC):
    """Интерфейс создателя файла отчёта."""
    items: List[ReportItem]

    def __init__(self, items: List[ReportItem]):
        self.items = items

    @abstractmethod
    def generate(self, file_path: Path) -> Path:
        raise NotImplemented


class ReportWriterDocx(ReportWriter):
    """Создатель файла отчёта в формате docx."""
    items: List[ReportItemDocx]

    def generate(self, file_path: Path):
        document = Document()
        for i, item in enumerate(self.items):
            p = document.add_paragraph()
            p.add_run(f"{str(i + 1)}.").bold = True
            item.write(document)
        document.save(str(file_path))


class ReportWriterCreator(ABC):
    """Интерфейс создателя генератора отчётов."""
    @staticmethod
    @abstractmethod
    def create(applications: List[dict], inid_data: List[InidCode]) -> ReportWriter:
        """
        Создаёт объект генератора отчётов.

        :param applications список заявок
        :param inid_data список кодов инид
        """
        raise NotImplemented


class ReportWriterDocxCreator(ReportWriterCreator):
    """Класс, задачей которого есть создание объекта генератора отчётов в формате .docx."""
    @staticmethod
    def create(applications: List[dict], inid_data: List[InidCode]) -> ReportWriterDocx:
        report_item_classes = {
            4: ReportItemDocxTM
        }
        report_items = []
        for app in applications:
            try:
                report_item = report_item_classes[app['Document']['idObjType']](
                    application_data=app,
                    ipc_fields=inid_data
                )
                report_items.append(report_item)
            except KeyError:
                continue
        return ReportWriterDocx(items=report_items)
