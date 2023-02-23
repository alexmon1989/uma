from apps.search.dataclasses import InidCode

from typing import List
from abc import ABC, abstractmethod
from pathlib import Path

from docx import Document
from docx.text.paragraph import Paragraph


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

    def _write_111(self) -> None:
        """Записывает номер свидетельства в документ."""
        inid = self._get_inid(self.obj_type_id, '111', self.application_data['search_data']['obj_state'])
        registration_number = self.application_data['TradeMark']['TrademarkDetails'].get('RegistrationNumber')
        if inid and inid.visible and registration_number:
            self._paragraph.add_run(f"({inid.code})").bold = True
            self._paragraph.add_run(f"\t{inid.title}: ")
            self._paragraph.add_run(registration_number).bold = True
            self._paragraph.add_run('\r')

    def write(self, document: Document) -> Paragraph:
        """Записывает информацию о ТМ в абзац и возвращает его."""
        self.document = document
        self._paragraph = self.document.add_paragraph('')

        self._write_111()

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
