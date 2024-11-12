from django.test import TestCase
from unittest.mock import patch

from apps.search.dataclasses import InidCode, ApplicationDocument
from apps.search.services import services, application_has_sanctions

from typing import List
from datetime import datetime, timedelta


class InidCodeGetListTestCase(TestCase):

    def test_valid_res_type(self):
        """Тестирует правильность типа данных возвращаемого результата."""
        res = services.inid_code_get_list(lang='ua')
        for item in res:
            self.assertEqual(type(item), InidCode)


def _set_application_documents(service: services.DownloadDocumentsService,
                               documents: List[ApplicationDocument]) -> None:
    service.documents = documents


class TestApplicationsCanBeIndexedTestCase(TestCase):
    def test_tm_can_be_indexed(self):
        """Тестирует может ли быть проиндексирована торговая марка."""
        # Заявка может быть проиндексирована всегда
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {}  # Отсутствует поле даты публикации
            }
        }
        self.assertTrue(services.application_tm_can_be_indexed(app_data))

        # Свидетельтво может быть проиндексировано если дата его публикации наступила и нет "будущих" оповещений
        tomorrow = datetime.now() + timedelta(1)
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "PublicationDetails": [
                        {
                            "PublicationDate": tomorrow.strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        self.assertFalse(services.application_tm_can_be_indexed(app_data))
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "PublicationDetails": [
                        {
                            "PublicationDate": datetime.now().strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        self.assertTrue(services.application_tm_can_be_indexed(app_data))
        app_data = {
            "TradeMark": {
                "Transactions": {
                    "Transaction": [
                        {
                            "@bulletinDate": tomorrow.strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        self.assertFalse(services.application_tm_can_be_indexed(app_data))

    def test_id_can_be_indexed(self):
        """Тестирует может ли быть проиндексирован пром. образец."""
        # Заявка может быть проиндексирована всегда
        app_data = {
            'Design': {
                'DesignDetails': {}  # Отсутствует поле даты публикации
            }
        }
        self.assertTrue(services.application_id_can_be_indexed(app_data))

        # Свидетельтво может быть проиндексировано если дата его публикации наступила и нет "будущих" оповещений
        tomorrow = datetime.now() + timedelta(1)
        app_data = {
            'Design': {
                'DesignDetails': {
                    "RecordPublicationDetails": [
                        {
                            "PublicationDate": tomorrow.strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        self.assertFalse(services.application_id_can_be_indexed(app_data))
        app_data = {
            'Design': {
                'DesignDetails': {
                    "RecordPublicationDetails": [
                        {
                            "PublicationDate": datetime.now().strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        self.assertTrue(services.application_id_can_be_indexed(app_data))
        app_data = {
            "Transactions": {
                "Transaction": [
                    {
                        "@bulletinDate": tomorrow.strftime('%Y-%m-%d')
                    }
                ]
            }
        }
        self.assertFalse(services.application_id_can_be_indexed(app_data))


class TestApplicationHasSanctions(TestCase):

    @patch('apps.search.services.services.gloc_get_sanctioned_objects')
    def test_no_app_number_and_reg_number(self, mock_gloc_get_sanctioned_objects):
        """Тест: оба номера (app_number и reg_number) не переданы."""
        result = application_has_sanctions(id_obj_type=1)
        self.assertFalse(result)
        mock_gloc_get_sanctioned_objects.assert_not_called()

    @patch('apps.search.services.services.gloc_get_sanctioned_objects')
    def test_invalid_id_obj_type(self, mock_gloc_get_sanctioned_objects):
        """Тест: id_obj_type отсутствует в gloc_obj_types."""
        result = application_has_sanctions(id_obj_type=999, app_number="12345")
        self.assertFalse(result)
        mock_gloc_get_sanctioned_objects.assert_not_called()

    @patch('apps.search.services.services.gloc_get_sanctioned_objects')
    def test_object_not_under_sanctions(self, mock_gloc_get_sanctioned_objects):
        """Тест: объект не находится под санкциями."""
        # Мокируем возвращаемое значение функции gloc_get_sanctioned_objects
        mock_gloc_get_sanctioned_objects.return_value = [
            {'obj_number': '99999', 'id_obj_type': 300},
            {'obj_number': '88888', 'id_obj_type': 301},
        ]

        result = application_has_sanctions(id_obj_type=1, app_number="12345", reg_number="54321")
        self.assertFalse(result)

    @patch('apps.search.services.services.gloc_get_sanctioned_objects')
    def test_object_under_sanctions_by_app_number(self, mock_gloc_get_sanctioned_objects):
        """Тест: объект находится под санкциями по app_number."""
        # Мокируем возвращаемое значение функции gloc_get_sanctioned_objects
        mock_gloc_get_sanctioned_objects.return_value = [
            {'obj_number': '12345', 'id_obj_type': 300},
            {'obj_number': '54321', 'id_obj_type': 301},
        ]

        result = application_has_sanctions(id_obj_type=1, app_number="12345")
        self.assertTrue(result)

    @patch('apps.search.services.services.gloc_get_sanctioned_objects')
    def test_object_under_sanctions_by_reg_number(self, mock_gloc_get_sanctioned_objects):
        """Тест: объект находится под санкциями по reg_number."""
        # Мокируем возвращаемое значение функции gloc_get_sanctioned_objects
        mock_gloc_get_sanctioned_objects.return_value = [
            {'obj_number': '54321', 'id_obj_type': 301},
            {'obj_number': '67890', 'id_obj_type': 300},
        ]

        result = application_has_sanctions(id_obj_type=1, reg_number="54321")
        self.assertTrue(result)

    @patch('apps.search.services.services.gloc_get_sanctioned_objects')
    def test_object_under_sanctions_with_different_type(self, mock_gloc_get_sanctioned_objects):
        """Тест: объект находится под санкциями, но тип не совпадает."""
        # Мокируем возвращаемое значение функции gloc_get_sanctioned_objects
        mock_gloc_get_sanctioned_objects.return_value = [
            {'obj_number': '12345', 'id_obj_type': 310},
        ]

        result = application_has_sanctions(id_obj_type=1, app_number="12345")
        self.assertFalse(result)
