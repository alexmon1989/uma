from django.test import TestCase
from django.conf import settings

from apps.search.models import IpcAppList


class TestIpcAppListTestCase(TestCase):

    def test_real_files_path_property(self):
        """Тестирует property real_files_path."""
        app = IpcAppList()
        app.files_path = '\\\\bear\\share\\INVENTIONS\\2023\\a202303880\\'
        self.assertEqual(
            app.real_files_path,
            f'{settings.DOCUMENTS_MOUNT_FOLDER}INVENTIONS/2023/a202303880/'
        )
        app.files_path = 'e:\\poznach_test_sis\\bear_tmpp_sis\\TRADEMARKS\\2023\\m202303880\\'
        self.assertEqual(
            app.real_files_path,
            f'{settings.DOCUMENTS_MOUNT_FOLDER}TRADEMARKS/2023/m202303880/'
        )
