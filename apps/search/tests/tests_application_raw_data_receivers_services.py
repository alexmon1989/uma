from django.test import TestCase
from apps.search.services.application_raw_data_receivers import (ApplicationRawDataReceiverService,
                                                                 ApplicationRawDataReceiverFilesystemService)


class TestApplicationRawDataReceiverFilesystemServiceTestCase(TestCase):
    """Тестирует класс ApplicationRawDataReceiverFilesystemService"""

    def setUp(self):
        self.service = ApplicationRawDataReceiverFilesystemService()

    def test_is_instance_of_abstract(self):
        """Тестирует является ли потомком базового класса."""
        self.assertIsInstance(self.service, ApplicationRawDataReceiverService)

    def test_get_data(self):
        pass
