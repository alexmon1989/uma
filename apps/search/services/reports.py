from apps.search.dataclasses import InidCode
from apps.bulletin.services import bulletin_get_number_441_code

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

    def __init__(self, application_data: dict, ipc_fields: List[InidCode], lang_code: str = 'ua'):
        self.application_data = application_data
        self.ipc_fields = ipc_fields
        self.lang_code = lang_code


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

    def _write_app_input_date(self) -> None:
        """Записывает в документ данные о поле "Дата надходження матеріалів заявки до НОІВ"."""
        inid = self._get_inid(self.obj_type_id, '221', self.application_data['search_data']['obj_state'])
        app_input_date = self.application_data['TradeMark']['TrademarkDetails'].get('app_input_date')
        if inid and inid.visible and app_input_date:
            app_date = datetime.strptime(app_input_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"{inid.title}: ")
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
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(goods_classes_str).bold = True
            for item in goods:
                self._paragraph.add_run('\r')
                self._paragraph.add_run(f"Кл. {item['ClassNumber']}:\t").bold = True
                terms = item['ClassificationTermDetails']['ClassificationTerm']
                values_str = '; '.join([x['ClassificationTermText'] for x in terms])
                self._paragraph.add_run(values_str)
            self._paragraph.add_run('\r')

    def _write_441(self) -> None:
        """Записывает в документ данные об ИНИД (441) Дата публікації відомостей про заявку та номер бюлетня."""
        inid = self._get_inid(self.obj_type_id, '441', self.application_data['search_data']['obj_state'])
        code_441 = self.application_data['TradeMark']['TrademarkDetails'].get('Code_441')
        if inid and inid.visible and code_441:
            bul_number = self.application_data['TradeMark']['TrademarkDetails'].get('Code_441_BulNumber')
            if not bul_number:
                bul_number = str(bulletin_get_number_441_code(code_441))

            code_441 = datetime.strptime(code_441, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(code_441).bold = True
            if self.lang_code == 'ua':
                self._paragraph.add_run(', бюл. №').bold = True
            else:
                self._paragraph.add_run(', bul. №').bold = True
            self._paragraph.add_run(bul_number).bold = True
            self._paragraph.add_run()
            self._paragraph.add_run('\r')

    def _write_450(self) -> None:
        """Записывает в документ данные об ИНИД (450) Дата публікації відомостей про видачу свідоцтва."""
        inid = self._get_inid(self.obj_type_id, '450', self.application_data['search_data']['obj_state'])
        publication_details = self.application_data['TradeMark']['TrademarkDetails'].get('PublicationDetails')
        if inid and inid.visible and publication_details and len(publication_details) > 0:
            bul_number = publication_details[0]['PublicationIdentifier']
            publication_date = datetime.strptime(
                publication_details[0]['PublicationDate'],
                '%Y-%m-%d'
            ).strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(publication_date).bold = True
            if self.lang_code == 'ua':
                self._paragraph.add_run(', бюл. № ').bold = True
            else:
                self._paragraph.add_run(', bul. № ').bold = True
            self._paragraph.add_run(bul_number).bold = True
            self._paragraph.add_run()
            self._paragraph.add_run('\r')

    def write(self, document: Document) -> Paragraph:
        """Записывает информацию о ТМ в абзац и возвращает его."""
        self.document = document
        self._paragraph = self.document.add_paragraph('')

        self._write_540()
        self._write_app_input_date()
        self._write_111()
        self._write_151()
        self._write_141()
        self._write_181()
        self._write_186()
        self._write_210()
        self._write_220()
        self._write_531()
        self._write_300()
        self._write_441()
        self._write_450()
        self._write_731()
        self._write_732()
        self._write_740()
        self._write_750()
        self._write_591()
        self._write_511()

        return self._paragraph


class ReportItemDocxMadrid(ReportItemDocx):
    """Торговая марка (Мадрид)."""
    _paragraph: Paragraph
    document: Document
    obj_type_id: int

    def _write_111(self) -> None:
        """Записывает в документ информацию об ИНИД (111) Номер міжнародної реєстрації."""
        inid = self._get_inid(self.obj_type_id, '111', self.application_data['search_data']['obj_state'])
        registration_number = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('@INTREGN')
        if inid and inid.visible and registration_number:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(registration_number).bold = True
            self._paragraph.add_run('\r')

    def _write_540(self) -> None:
        """Записывает в документ информацию об ИНИД (540) Зображення торговельної марки."""
        inid = self._get_inid(self.obj_type_id, '540', self.application_data['search_data']['obj_state'])
        if inid and inid.visible:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            self._paragraph.add_run('\r')

            # Зображення
            try:
                path = Path(self.application_data['Document']['filesPath'].replace('\\', '/'))
            except KeyError:
                pass
            else:
                parts_len = len(path.parts)
                # Путь к изображению на диске
                mark_image_filepath = Path(settings.MEDIA_ROOT) / path.parts[parts_len - 4].upper()
                mark_image_filepath /= mark_image_filepath / path.parts[parts_len - 3]
                mark_image_filepath /= mark_image_filepath / path.parts[parts_len - 2]
                mark_image_filepath /= path.parts[parts_len - 1]
                registration_number = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('@INTREGN')
                mark_image_filepath /= f"{registration_number}.jpg"
                run = self._paragraph.add_run()
                run.add_picture(str(mark_image_filepath), width=Inches(2.5))
                self._paragraph.add_run('\r')

    def _write_151(self) -> None:
        """Записывает в документ информацию об ИНИД (151) Дата міжнародної реєстрації."""
        inid = self._get_inid(self.obj_type_id, '151', self.application_data['search_data']['obj_state'])
        registration_date = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('@INTREGD')
        if inid and inid.visible and registration_date:
            registration_date = datetime.strptime(registration_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(registration_date).bold = True
            self._paragraph.add_run('\r')

    def _write_180(self) -> None:
        """Записывает в документ информацию об
        ИНИД (180) Очікувана дата закінчення строку дії реєстрації/продовження."""
        inid = self._get_inid(self.obj_type_id, '180', self.application_data['search_data']['obj_state'])
        exp_date = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('@INTREGD')
        if inid and inid.visible and exp_date:
            exp_date = datetime.strptime(exp_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(exp_date).bold = True
            self._paragraph.add_run('\r')

    def _write_441(self) -> None:
        """Записывает в документ информацию об
        ИНИД (441) Дата публікації відомостей про міжнародну реєстрацію торговельної марки,
        що надійшла для проведення експертизи."""
        inid = self._get_inid(self.obj_type_id, '441', self.application_data['search_data']['obj_state'])
        code_441 = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('Code_441')
        if inid and inid.visible and code_441:
            bul_number = str(bulletin_get_number_441_code(code_441))
            code_441 = datetime.strptime(code_441, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(code_441).bold = True
            if self.lang_code == 'ua':
                self._paragraph.add_run(', бюл. № ').bold = True
            else:
                self._paragraph.add_run(', bul. № ').bold = True
            self._paragraph.add_run(bul_number).bold = True
            self._paragraph.add_run()
            self._paragraph.add_run('\r')

    def _write_450(self) -> None:
        """Записывает в документ информацию об
        ИНИД (450) Дата публікації відомостей про міжнародну реєстрацію та номер бюлетеню Міжнародного бюро ВОІВ"""
        inid = self._get_inid(self.obj_type_id, '450', self.application_data['search_data']['obj_state'])
        pub_date = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('ENN', {}).get('@PUBDATE')
        if inid and inid.visible and pub_date:
            pub_date = datetime.strptime(pub_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            bul_number = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('ENN', {}).get('@GAZNO')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(pub_date).bold = True
            if self.lang_code == 'ua':
                self._paragraph.add_run(', бюл. № ').bold = True
            else:
                self._paragraph.add_run(', bul. № ').bold = True
            self._paragraph.add_run(bul_number).bold = True
            self._paragraph.add_run()
            self._paragraph.add_run('\r')

    def _write_732(self) -> None:
        """Записывает в документ информацию об
        ИНИД (732) Ім'я та адреса володільця реєстрації."""
        inid = self._get_inid(self.obj_type_id, '732', self.application_data['search_data']['obj_state'])
        holder = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('HOLGR')
        if inid and inid.visible and holder:
            holder_name = holder.get('NAME', {}).get('NAMEL')
            holder_address = '\n'.join([x for x in holder.get('ADDRESS', {}).get('ADDRL', [])])
            holder_country = holder.get('ADDRESS', {}).get('COUNTRY')

            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:\n")

            self._paragraph.add_run(holder_name).bold = True
            self._paragraph.add_run('\r')

            self._paragraph.add_run(holder_address)
            self._paragraph.add_run('\r')

            self._paragraph.add_run(f"({holder_country})")
            self._paragraph.add_run('\r')

    def _write_740(self) -> None:
        """Записывает в документ информацию об
        ИНИД (740) Ім'я та адреса представника."""
        inid = self._get_inid(self.obj_type_id, '740', self.application_data['search_data']['obj_state'])
        representative = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('REPGR')
        if inid and inid.visible and representative:
            representative_name = representative.get('NAME', {}).get('NAMEL')
            representative_address = '\n'.join([x for x in representative.get('ADDRESS', {}).get('ADDRL', [])])
            representative_country = representative.get('ADDRESS', {}).get('COUNTRY')

            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:\n")

            self._paragraph.add_run(representative_name).bold = True
            self._paragraph.add_run('\r')

            self._paragraph.add_run(representative_address)
            self._paragraph.add_run('\r')

            self._paragraph.add_run(f"({representative_country})")
            self._paragraph.add_run('\r')

    def _write_821(self) -> None:
        """Записывает в документ информацию об
        ИНИД (821) Базова заявка."""
        inid = self._get_inid(self.obj_type_id, '821', self.application_data['search_data']['obj_state'])
        base_app = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('BASGR', {}).get('BASAPPGR')
        if inid and inid.visible and base_app:
            app_date = datetime.strptime(base_app['BASAPPD'], '%Y-%m-%d').strftime('%d.%m.%Y')

            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(f"{app_date}, ").bold = True
            self._paragraph.add_run(base_app['BASAPPN']).bold = True
            self._paragraph.add_run('\r')

    def _write_891(self) -> None:
        """Записывает в документ информацию об
        ИНИД (891) Дата територіального поширення міжнародної реєстрації."""
        inid = self._get_inid(self.obj_type_id, '891', self.application_data['search_data']['obj_state'])
        reg_date = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('@REGEDAT')
        if inid and inid.visible and reg_date:
            reg_date = datetime.strptime(reg_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(f"{reg_date}, ").bold = True
            self._paragraph.add_run('\r')

    def _write_511(self) -> None:
        """Записывает в документ информацию об
        ИНИД (511) Індекс (індекси) МКТП та перелік товарів і послуг."""
        inid = self._get_inid(self.obj_type_id, '511', self.application_data['search_data']['obj_state'])
        gsgr = self.application_data['MadridTradeMark']['TradeMarkDetails'].get('BASICGS', {}).get('GSGR')
        if inid and inid.visible and gsgr:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            for cl in gsgr:
                self._paragraph.add_run(f"\nКл. {cl.get('@NICCLAI')}: ").bold = True
                self._paragraph.add_run(cl.get('GSTERMEN'))
            self._paragraph.add_run('\r')

    def write(self, document: Document) -> Paragraph:
        """Записывает информацию о ТМ в абзац и возвращает его."""
        self.document = document
        self._paragraph = self.document.add_paragraph('')

        self._write_540()
        self._write_111()
        self._write_151()
        self._write_180()
        self._write_441()
        self._write_450()
        self._write_732()
        self._write_740()
        self._write_821()
        self._write_891()
        self._write_511()

        return self._paragraph


class ReportItemDocxMadrid9(ReportItemDocxMadrid):
    obj_type_id = 9


class ReportItemDocxMadrid14(ReportItemDocxMadrid):
    obj_type_id = 14


class ReportItemDocxID(ReportItemDocx):
    """Торговая марка."""
    _paragraph: Paragraph
    document: Document
    obj_type_id = 6

    def _write_21(self) -> None:
        """Записывает в документ данные об ИНИД (21) Номер заявки."""
        inid = self._get_inid(self.obj_type_id, '21', self.application_data['search_data']['obj_state'])
        app_number = self.application_data['Design']['DesignDetails'].get('DesignApplicationNumber')
        if inid and inid.visible and app_number:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(app_number).bold = True
            self._paragraph.add_run('\r')

    def _write_51(self) -> None:
        """Записывает в документ данные об
        ИНИД (51) Індекс(и) Міжнародної класифікації промислових зразків (МКПЗ)."""
        inid = self._get_inid(self.obj_type_id, '51', self.application_data['search_data']['obj_state'])
        classes = self.application_data['Design']['DesignDetails'].get('IndicationProductDetails')
        if inid and inid.visible and classes:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(', '.join([x['Class'] for x in classes])).bold = True
            self._paragraph.add_run('\r')

    def _write_11(self) -> None:
        """Записывает в документ данные об
        ИНИД (11) Номер реєстрації (патенту)."""
        inid = self._get_inid(self.obj_type_id, '11', self.application_data['search_data']['obj_state'])
        reg_number = self.application_data['Design']['DesignDetails'].get('RegistrationNumber')
        if inid and inid.visible and reg_number:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(reg_number).bold = True
            self._paragraph.add_run('\r')

    def _write_22(self) -> None:
        """Записывает в документ данные об
        ИНИД (22) Дата подання заявки."""
        inid = self._get_inid(self.obj_type_id, '22', self.application_data['search_data']['obj_state'])
        app_date = self.application_data['Design']['DesignDetails'].get('DesignApplicationDate')
        if inid and inid.visible and app_date:
            app_date = datetime.strptime(app_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(app_date).bold = True
            self._paragraph.add_run('\r')

    def _write_23(self) -> None:
        """Записывает в документ данные об
        ИНИД (23) Дата виставкового пріоритету."""
        inid = self._get_inid(self.obj_type_id, '23', self.application_data['search_data']['obj_state'])
        priority = self.application_data['Design']['DesignDetails'].get('ExhibitionPriorityDetails')
        if inid and inid.visible and priority and len(priority) > 0:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:\r")

            for item in priority:
                exhibition_date = datetime.strptime(item['ExhibitionDate'], '%Y-%m-%d').strftime('%d.%m.%Y')
                self._paragraph.add_run(exhibition_date).bold = True
                self._paragraph.add_run('; ')
                self._paragraph.add_run(item['ExhibitionCountryCode'])
                self._paragraph.add_run('\r')

            self._paragraph.add_run('\r')

    def _write_24(self) -> None:
        """Записывает в документ данные об
        ИНИД (24) Дата, з якої є чинними права на промисловий зразок."""
        inid = self._get_inid(self.obj_type_id, '24', self.application_data['search_data']['obj_state'])
        reg_date = self.application_data['Design']['DesignDetails'].get('RecordEffectiveDate')
        if inid and inid.visible and reg_date:
            reg_date = datetime.strptime(reg_date, '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(reg_date).bold = True
            self._paragraph.add_run('\r')

    def _write_28(self) -> None:
        """Записывает в документ данные об
        ИНИД (28) Кількість заявлених варіантів."""
        inid = self._get_inid(self.obj_type_id, '28', self.application_data['search_data']['obj_state'])
        total_specimen = self.application_data['Design']['DesignDetails'].get('TotalSpecimen')
        if inid and inid.visible and total_specimen:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(str(total_specimen)).bold = True
            self._paragraph.add_run('\r')

    def _write_31(self) -> None:
        """Записывает в документ данные об
        ИНИД (31) Номер попередньої заявки відповідно до Паризької конвенції."""
        inid = self._get_inid(self.obj_type_id, '31', self.application_data['search_data']['obj_state'])
        priority = self.application_data['Design']['DesignDetails'].get('PriorityDetails', {}).get('Priority')
        if inid and inid.visible and priority and len(priority) > 0:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(priority[0]['PriorityNumber']).bold = True
            self._paragraph.add_run('\r')

    def _write_32(self) -> None:
        """Записывает в документ данные об
        ИНИД (32) Дата подання попередньої заявки відповідно до Паризької конвенції."""
        inid = self._get_inid(self.obj_type_id, '32', self.application_data['search_data']['obj_state'])
        priority = self.application_data['Design']['DesignDetails'].get('PriorityDetails', {}).get('Priority')
        if inid and inid.visible and priority and len(priority) > 0:
            priority_date = datetime.strptime(priority[0]['PriorityDate'], '%Y-%m-%d').strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(priority_date).bold = True
            self._paragraph.add_run('\r')

    def _write_33(self) -> None:
        """Записывает в документ данные об
        ИНИД (33) Двобуквений код держави-учасниці Паризької конвенції, до якої подано попередню заявку."""
        inid = self._get_inid(self.obj_type_id, '33', self.application_data['search_data']['obj_state'])
        priority = self.application_data['Design']['DesignDetails'].get('PriorityDetails', {}).get('Priority')
        if inid and inid.visible and priority and len(priority) > 0:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(priority[0]['PriorityCountryCode']).bold = True
            self._paragraph.add_run('\r')

    def _write_45(self) -> None:
        """Записывает в документ данные об ИНИД (45) Дата публікації відомостей про видачу патенту та номер бюлетеня."""
        inid = self._get_inid(self.obj_type_id, '45', self.application_data['search_data']['obj_state'])
        publication_details = self.application_data['Design']['DesignDetails'].get('RecordPublicationDetails')
        if inid and inid.visible and publication_details and len(publication_details) > 0:
            bul_number = publication_details[0]['PublicationIdentifier']
            publication_date = datetime.strptime(
                publication_details[0]['PublicationDate'],
                '%Y-%m-%d'
            ).strftime('%d.%m.%Y')
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(publication_date).bold = True
            if self.lang_code == 'ua':
                self._paragraph.add_run(', бюл. № ').bold = True
            else:
                self._paragraph.add_run(', bul. № ').bold = True
            self._paragraph.add_run(bul_number).bold = True
            self._paragraph.add_run()
            self._paragraph.add_run('\r')

    def _write_54(self) -> None:
        """Записывает в документ данные об
        ИНИД (54) Назва промислового зразка."""
        inid = self._get_inid(self.obj_type_id, '54', self.application_data['search_data']['obj_state'])
        title = self.application_data['Design']['DesignDetails'].get('DesignTitle')
        if inid and inid.visible and title:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(title).bold = True
            self._paragraph.add_run('\r')

    def _write_55(self) -> None:
        """Записывает в документ данные об
        ИНИД (55) Назва промислового зразка."""
        inid = self._get_inid(self.obj_type_id, '55', self.application_data['search_data']['obj_state'])
        specimen_details = self.application_data['Design']['DesignDetails'].get('DesignSpecimenDetails')
        if inid and inid.visible and specimen_details:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            for i, item in enumerate(specimen_details):
                if 'Colors' in item:
                    self._paragraph.add_run('\r')
                    self._paragraph.add_run(f"{i + 1}-й варіант - {item['Colors']['Color']}").bold = True
            self._paragraph.add_run("\r")

            for specimen in specimen_details:
                for image in specimen['DesignSpecimen']:
                    self._paragraph.add_run(image['SpecimenIndex'])
                    self._paragraph.add_run(':\r')
                    path = Path(self.application_data['Document']['filesPath'].replace('\\', '/'))
                    parts_len = len(path.parts)
                    # Путь к изображению на диске
                    mark_image_filepath = Path(settings.MEDIA_ROOT) / path.parts[parts_len - 3]
                    mark_image_filepath /= mark_image_filepath / path.parts[parts_len - 2]
                    mark_image_filepath /= path.parts[parts_len - 1]
                    mark_image_filepath /= image['SpecimenFilename']
                    run = self._paragraph.add_run()
                    run.add_picture(str(mark_image_filepath), width=Inches(2.5))
                    self._paragraph.add_run('\r')

    def _write_71(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (71) Ім'я (імена) та адреса (адреси) заявника (заявників)
        """
        inid = self._get_inid(self.obj_type_id, '71', self.application_data['search_data']['obj_state'])
        applicants = self.application_data['Design']['DesignDetails'].get(
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

                self._paragraph.add_run('\r')
                try:
                    self._paragraph.add_run(
                        applicant['ApplicantAddressBook']['FormattedNameAddress']['Address']['FreeFormatAddress'][
                            'FreeFormatAddressLine']
                    )
                except KeyError:
                    pass

            self._paragraph.add_run('\r')

    def _write_72(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (72) Ім'я (імена) автора (авторів), якщо воно відоме
        """
        inid = self._get_inid(self.obj_type_id, '72', self.application_data['search_data']['obj_state'])
        designers = self.application_data['Design']['DesignDetails'].get(
            'DesignerDetails', {}
        ).get(
            'Designer'
        )
        if inid and inid.visible and designers:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            for designer in designers:
                if designer.get('Publicated'):
                    self._paragraph.add_run('\r')
                    try:
                        self._paragraph.add_run(
                            designer['DesignerAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                                'FreeFormatNameDetails']['FreeFormatNameLine']
                        ).bold = True
                    except KeyError:
                        pass

            self._paragraph.add_run('\r')

    def _write_73(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (73) Ім’я або повне найменування власника(ів) патенту, його адреса та двобуквений код держави
        """
        inid = self._get_inid(self.obj_type_id, '73', self.application_data['search_data']['obj_state'])
        holders = self.application_data['Design']['DesignDetails'].get(
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

                self._paragraph.add_run('\r')
                try:
                    country = holder['HolderAddressBook']['FormattedNameAddress']['Address'][
                        'AddressCountryCode']
                    self._paragraph.add_run(
                        f"({country})"
                    )
                except KeyError:
                    pass

            self._paragraph.add_run('\r')

    def _write_74(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (74) Ім'я (імена) та адреса (адреси) представника (представників)
        """
        inid = self._get_inid(self.obj_type_id, '74', self.application_data['search_data']['obj_state'])
        representatives = self.application_data['Design']['DesignDetails'].get(
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
                            'FreeFormatNameDetails']['FreeFormatNameLine']
                    ).bold = True
                except KeyError:
                    pass

                self._paragraph.add_run('\r')
                try:
                    self._paragraph.add_run(
                        representative['RepresentativeAddressBook']['FormattedNameAddress']['Address']['FreeFormatAddress'][
                            'FreeFormatAddressLine']
                    )
                except KeyError:
                    pass

            self._paragraph.add_run('\r')

    def _write_98(self) -> None:
        """
        Записывает в документ
        данные об ИНИД (98) Адреса для листування
        """
        inid = self._get_inid(self.obj_type_id, '98', self.application_data['search_data']['obj_state'])
        correspondence = self.application_data['Design']['DesignDetails'].get(
            'CorrespondenceAddress'
        )
        if inid and inid.visible and correspondence:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}:")
            self._paragraph.add_run('\r')
            try:
                self._paragraph.add_run(
                    correspondence['CorrespondenceAddressBook']['FormattedNameAddress']['Name']['FreeFormatName'][
                        'FreeFormatNameDetails']['FreeFormatNameLine']
                ).bold = True
            except KeyError:
                pass

            self._paragraph.add_run('\r')
            try:
                self._paragraph.add_run(
                    correspondence['CorrespondenceAddressBook']['FormattedNameAddress']['Address']['FreeFormatAddress'][
                        'FreeFormatAddressLine']
                )
            except KeyError:
                pass

            self._paragraph.add_run('\r')
            try:
                country = correspondence['CorrespondenceAddressBook']['FormattedNameAddress']['Address'][
                    'AddressCountryCode']
                self._paragraph.add_run(
                    f"({country})"
                )
            except KeyError:
                pass

            self._paragraph.add_run('\r')

    def write(self, document: Document) -> Paragraph:
        """Записывает информацию о ТМ в абзац и возвращает его."""
        self.document = document
        self._paragraph = self.document.add_paragraph('')

        self._write_51()
        self._write_11()
        self._write_21()
        self._write_22()
        self._write_23()
        self._write_24()
        self._write_31()
        self._write_32()
        self._write_33()
        self._write_45()
        self._write_54()
        self._write_55()
        self._write_71()
        self._write_72()
        self._write_73()
        self._write_74()
        self._write_98()

        self._write_28()

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
    def create(applications: List[dict], inid_data: List[InidCode], lang_code: str) -> ReportWriter:
        """
        Создаёт объект генератора отчётов.

        :param applications список заявок
        :param inid_data список кодов инид
        """
        raise NotImplemented


class ReportWriterDocxCreator(ReportWriterCreator):
    """Класс, задачей которого есть создание объекта генератора отчётов в формате .docx."""
    @staticmethod
    def create(applications: List[dict], inid_data: List[InidCode], lang_code: str = 'ua') -> ReportWriterDocx:
        report_item_classes = {
            4: ReportItemDocxTM,
            6: ReportItemDocxID,
            9: ReportItemDocxMadrid9,
            14: ReportItemDocxMadrid14,
        }
        report_items = []
        for app in applications:
            try:
                report_item = report_item_classes[app['Document']['idObjType']](
                    application_data=app,
                    ipc_fields=inid_data,
                    lang_code=lang_code,
                )
                report_items.append(report_item)
            except KeyError:
                continue
        return ReportWriterDocx(items=report_items)
