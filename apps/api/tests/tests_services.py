from django.test import TestCase
from unittest.mock import patch

from rest_framework import exceptions

from apps.api.services import services

from datetime import datetime


class ApiServicesTestCase(TestCase):

    def test_opendata_prepare_filters(self):
        """Тестирует функцию opendata_prepare_filters (подготовка фильтров)."""
        filters = (
            'obj_state',
            'obj_type',
            'app_date_from',
            'app_date_to',
            'reg_date_from',
            'reg_date_to',
            'last_update_from',
            'last_update_to',
            'app_number',
        )
        input_data = {}
        output_data = services.opendata_prepare_filters(input_data)
        # Если значение фильтра отсутствует во вх. данных, то его и не должно быть в исходящих
        for key in filters:
            self.assertNotIn(key, output_data)

        # Целочисленные фильтры
        filters = (
            'obj_state',
            'obj_type',
        )
        for key in filters:
            input_data = {key: 1}
            output_data = services.opendata_prepare_filters(input_data)
            self.assertEqual(output_data[key], 1)

            input_data = {key: '1'}
            output_data = services.opendata_prepare_filters(input_data)
            self.assertEqual(output_data[key], 1)

            input_data = {key: 'qwe'}
            with self.assertRaisesRegex(exceptions.ParseError, f'Невірне значення параметру {key}'):
                services.opendata_prepare_filters(input_data)

        # Фильтры даты
        filters = (
            'app_date_from',
            'app_date_to',
            'reg_date_from',
            'reg_date_to',
            'last_update_from',
            'last_update_to',
        )
        d = datetime.strptime('21.03.2023', '%d.%m.%Y')
        for key in filters:
            input_data = {key: '21.03.2023'}
            output_data = services.opendata_prepare_filters(input_data)
            self.assertEqual(output_data[key], d)

            input_data = {key: '21/03/2023'}
            with self.assertRaisesRegex(exceptions.ParseError, f'Невірне значення параметру {key}'):
                services.opendata_prepare_filters(input_data)

            input_data = {key: 'abcde'}
            with self.assertRaisesRegex(exceptions.ParseError, f'Невірне значення параметру {key}'):
                services.opendata_prepare_filters(input_data)

            input_data = {key: 123}
            with self.assertRaisesRegex(exceptions.ParseError, f'Невірне значення параметру {key}'):
                services.opendata_prepare_filters(input_data)

        input_data = {'app_number': 'm202300001'}
        output_data = services.opendata_prepare_filters(input_data)
        self.assertEqual(output_data['app_number'], 'm202300001')
