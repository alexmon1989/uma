from django.test import TestCase
from unittest.mock import patch
from apps.search.dataclasses import InidCode, ApplicationDocument
from apps.search.services import services

from typing import List
from datetime import datetime


class InidCodeGetListTestCase(TestCase):

    def test_valid_res_type(self):
        """Тестирует правильность типа данных возвращаемого результата."""
        res = services.inid_code_get_list(lang='ua')
        for item in res:
            self.assertEqual(type(item), InidCode)


def _set_application_documents(service: services.DownloadDocumentsService,
                               documents: List[ApplicationDocument]) -> None:
    service.documents = documents


class DownloadDocumentsServiceTestCase(TestCase):
    """Тестирует сервис загрузки из ЦЕАД документов заявки пользователем."""

    @patch('apps.search.services.services.DownloadDocumentsService._set_application_documents')
    def test_check_correct_cead_id(self, mock_set_application_documents):
        """Тестирует функцию проверки все ли документы принадлежат заявке."""
        service = services.DownloadDocumentsService()
        documents = [
            ApplicationDocument(title='Рішення про реєстрацію знака (Т-8)', reg_number='123', id_doc_cead=123),
            ApplicationDocument(title='Форма Т-19 Рішення за заявкою', reg_number='456', id_doc_cead=456),
            ApplicationDocument(title='Лист', reg_number='789', id_doc_cead=789),
        ]
        mock_set_application_documents.side_effect = _set_application_documents(
            service, documents
        )
        res = service.execute([123, 456, 789, 111], 1)
        self.assertEqual(res.error.error_type, 'wrong_id_doc_cead_list')

    @patch('apps.search.services.services.DownloadDocumentsService._set_application_documents')
    @patch('apps.search.services.services.document_get_receive_date_cead')
    def test_check_receive_date(self, mock_document_get_receive_date_cead, mock_set_application_documents):
        """Тестирует функцию проверки есть ли дата получения у документов типов Т-8, Т-19, П-8, П-19."""
        mock_document_get_receive_date_cead.return_value = None
        service = services.DownloadDocumentsService()
        documents = [
            ApplicationDocument(title='Рішення про реєстрацію знака (Т-8)', reg_number='1', id_doc_cead=1),
            ApplicationDocument(title='Форма Т-19 Рішення за заявкою', reg_number='2', id_doc_cead=2),
            ApplicationDocument(title='Форма П-8', reg_number='3', id_doc_cead=3),
            ApplicationDocument(title='Форма П-19', reg_number='4', id_doc_cead=4),
            ApplicationDocument(title='Лист', reg_number='5', id_doc_cead=5),
        ]
        mock_set_application_documents.side_effect = _set_application_documents(
            service, documents
        )
        res = service.execute([1, 2, 3, 5], 1)
        self.assertEqual(mock_document_get_receive_date_cead.call_count, 3)
        self.assertEqual(res.error.error_type, 'no_receive_date')
        self.assertIn(documents[0], service.documents_wo_receive_date)
        self.assertIn(documents[1], service.documents_wo_receive_date)
        self.assertIn(documents[2], service.documents_wo_receive_date)
        self.assertNotIn(documents[3], service.documents_wo_receive_date)
        self.assertNotIn(documents[4], service.documents_wo_receive_date)

        mock_document_get_receive_date_cead.return_value = datetime.now()
        res = service.execute([1, 2, 3], 1)
        self.assertEqual(res.status, 'success')
        self.assertEqual(len(service.documents_wo_receive_date), 0)
