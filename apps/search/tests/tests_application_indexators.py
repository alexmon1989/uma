import json

from django.test import TestCase
from apps.search.services.application_indexators import ApplicationIndexationService
from apps.search.services.application_raw_data_receivers import ApplicationRawDataReceiverFilesystemService
from apps.search.services.application_raw_data_fixers import ApplicationRawDataFixerService
from apps.search.services.application_simple_data_creators import ApplicationSimpleDataCreatorService
from apps.search.models import IpcAppList


class TestApplicationRawDataReceiverFilesystemServiceTestCase(TestCase):
    """Тестирует класс ApplicationRawDataReceiverFilesystemService"""

    def test_receives_raw_data(self):
        """Тестирует получение сырых данных."""
        expected = {'test': 'data'}
        with open('/tmp/m202400001.json', 'w') as fp:
            json.dump(expected, fp)

        service = ApplicationIndexationService(
            app_data_receiver=ApplicationRawDataReceiverFilesystemService(),
            app_simple_data_creator=ApplicationSimpleDataCreatorService()
        )

        app = IpcAppList(app_number='m202400001', files_path='/tmp/')
        service._app = app
        service._receive_raw_data()

        self.assertDictEqual(expected, service._index_data)
