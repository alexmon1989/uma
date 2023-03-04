from django.test import TestCase
from apps.search.dataclasses import InidCode
from apps.search.services import services


class InidCodeGetListTestCase(TestCase):

    def test_valid_res_type(self):
        """Тестирует правильность типа данных возвращаемого результата."""
        res = services.inid_code_get_list(lang='ua')
        for item in res:
            self.assertEqual(type(item), InidCode)
