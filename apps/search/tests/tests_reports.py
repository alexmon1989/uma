from django.test import TestCase
from apps.search.services.reports import ReportItemDocxTM, ReportWriterDocx
from apps.search.dataclasses import InidCode

from docx import Document

from pathlib import Path
import tempfile


class ReportItemDocxTmTestCase(TestCase):
    def setUp(self) -> None:
        self.document = Document()

    def test_inid_111(self):
        """Тестирует корректность добавления информации о номере регистрации."""
        # Номер регистрации есть в данных и разрешён для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationNumber': '111111'
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode('111', 'Номер свідоцтва', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertTrue('(111)\tНомер свідоцтва: 111111' in p.text)

        # Номер регистрации есть в данных и не разрешён для отображения
        inid_data = [
            InidCode('111', 'Номер свідоцтва', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertFalse('(111)\tНомер свідоцтва: 111111' in p.text)

        # Номера регистрации нет данных, разрешён для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode('111', 'Номер свідоцтва', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertFalse('(111)\tНомер свідоцтва: 111111' in p.text)


class ReportWriterDocxTestCase(TestCase):
    """Тестирует класс создания файла отчёта в формате .docx."""
    report_path = Path(tempfile.gettempdir()) / 'report.docx'
    # report_path = Path('report.docx')

    def test_generates_report(self):
        """Тестирует создание отчёта."""
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationNumber': '111111'
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode('111', 'Номер свідоцтва', 2, True)
        ]
        items = [ReportItemDocxTM(biblio_data, inid_data)]

        file_path = Path(tempfile.gettempdir()) / 'report.docx'
        writer = ReportWriterDocx(items)
        writer.generate(file_path)
        self.assertTrue(file_path.exists())
