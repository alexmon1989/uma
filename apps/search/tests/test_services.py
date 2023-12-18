from django.test import TestCase
from apps.search.dataclasses import InidCode, ApplicationDocument
from apps.search.services import services

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
