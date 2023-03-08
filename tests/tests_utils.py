from django.test import TestCase
from uma import utils

from unittest import mock


class ReportItemDocxTmTestCase(TestCase):
    @mock.patch('uma.utils.get_datetime_now_str')
    def test_get_unique_filename(self, mock_get_datetime_now_str):
        mock_get_datetime_now_str.return_value = '230308_144355'

        file_name = utils.get_unique_filename('test')
        self.assertEqual(file_name, 'test_230308_144355')

        file_name = utils.get_unique_filename('test1/test2')
        self.assertEqual(file_name, 'test1_test2_230308_144355')
