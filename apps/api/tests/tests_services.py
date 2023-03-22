from django.test import TestCase

from rest_framework import exceptions

from apps.api.services import services
from apps.api.models import OpenData

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

    def test_opendata_get_list_queryset(self):
        """Тестирует функцию opendata_get_list_queryset (формирование Queryset для получения данных из API)."""
        base_qs = OpenData.objects.select_related('obj_type').order_by('pk').all()

        # Проверка фильтров
        filters = {'obj_state': 1}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(obj_state=1)
        self.assertEqual(str(queryset.query), str(expected.query))

        filters = {'obj_type': 1}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(obj_type=1)
        self.assertEqual(str(queryset.query), str(expected.query))

        filters = {'app_date_from': datetime.strptime('21.03.2023', '%d.%m.%Y')}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(app_date__gte=filters['app_date_from'].replace(hour=0, minute=0, second=0))
        self.assertEqual(str(queryset.query), str(expected.query))

        filters = {'app_date_to': datetime.strptime('21.03.2023', '%d.%m.%Y')}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(app_date__lte=filters['app_date_to'].replace(hour=23, minute=59, second=59))
        self.assertEqual(str(queryset.query), str(expected.query))

        filters = {'reg_date_from': datetime.strptime('21.03.2023', '%d.%m.%Y')}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(registration_date__gte=filters['reg_date_from'].replace(hour=0, minute=0, second=0))
        self.assertEqual(str(queryset.query), str(expected.query))

        filters = {'reg_date_to': datetime.strptime('21.03.2023', '%d.%m.%Y')}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(registration_date__lte=filters['reg_date_to'].replace(hour=23, minute=59, second=59))
        self.assertEqual(str(queryset.query), str(expected.query))

        filters = {'last_update_from': datetime.strptime('21.03.2023', '%d.%m.%Y')}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(last_update__gte=filters['last_update_from'].replace(hour=0, minute=0, second=0))
        self.assertEqual(str(queryset.query), str(expected.query))

        filters = {'last_update_to': datetime.strptime('21.03.2023', '%d.%m.%Y')}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(last_update__lte=filters['last_update_to'].replace(hour=23, minute=59, second=59))
        self.assertEqual(str(queryset.query), str(expected.query))

        filters = {'app_number': 'm202100001'}
        queryset = services.opendata_get_list_queryset(filters)
        expected = base_qs.filter(app_number=filters['app_number'])
        self.assertEqual(str(queryset.query), str(expected.query))
