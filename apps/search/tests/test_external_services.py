import datetime

from django.test import TestCase
from unittest.mock import patch, MagicMock

from apps.search.services.external import gloc_get_sanctioned_objects, CeadLimitsService


class TestGlocGetSanctionedObjects(TestCase):
    """Тестує отримання підсанкційних об'єктів з БД GLOC"""

    @patch('apps.search.services.external.cache')
    def test_gloc_get_sanctioned_objects_from_cache(self, mock_cache):
        """Тестує отримання даних з кешу."""

        # Підготовка даних
        mock_cache.get.return_value = [{'obj_number': 'a202400001', 'id_obj_type': 300}]

        # Виклик функції
        result = gloc_get_sanctioned_objects()

        # Перевірка результата
        self.assertEqual(result, [{'obj_number': 'a202400001', 'id_obj_type': 300}])
        mock_cache.get.assert_called_once_with("rr_sanctioned_objects")

    @patch('apps.search.services.external.connections')
    @patch('apps.search.services.external.cache')
    def test_gloc_get_sanctioned_objects_from_db(self, mock_cache, mock_connections):
        """Тестує отримання даних із БД и збереження їх у кеш."""
        # Встановлення пустого кеша
        mock_cache.get.return_value = None

        # Налаштування курсора БД
        mock_cursor = MagicMock()
        mock_connections['gloc'].cursor.return_value.__enter__.return_value = mock_cursor

        # Налаштування даних, що повертаються курсором
        mock_cursor.fetchall.return_value = [
            ('a202400001', 300),
            ('12345', 301),
        ]

        # Виклик функції
        result = gloc_get_sanctioned_objects()

        # Перевірка SQL-запита
        mock_cursor.execute.assert_called_once_with(
            "SELECT DISTINCT ObjNumber, idObjType FROM rr_sanctioned_objects WHERE idState = 125 ORDER BY idObjType"
        )

        # Перевірка результату
        expected_result = [
            {'obj_number': 'a202400001', 'id_obj_type': 300},
            {'obj_number': '12345', 'id_obj_type': 301},
        ]
        self.assertEqual(result, expected_result)

        # Перевірка, що дані було закешовано
        mock_cache.set.assert_called_once_with("rr_sanctioned_objects", expected_result, 3600)


class CeadLimitsServiceTests(TestCase):
    def setUp(self):
        self.service = CeadLimitsService()

    @patch('apps.search.services.external.connections')
    def test_get_list_returns_correct_results(self, mock_connections):
        """Тест метода get_list для коректного повернення даних за період."""
        mock_cursor = MagicMock()
        mock_connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        # Эмулируем возвращаемые данные курсора
        mock_cursor.fetchone.side_effect = [
            ('a202400001', 1),
            ('u202400002', 8),
            None  # Кінець даних
        ]

        datetime_from = datetime.datetime(2024, 1, 1, 0, 0, 0)
        datetime_to = datetime.datetime(2024, 1, 31, 23, 59, 59)

        result = self.service.get_list(datetime_from, datetime_to)

        expected_result = [
            ('a202400001', 1),
            ('u202400002', 2),
        ]
        self.assertEqual(result, expected_result)

    @patch('apps.search.services.external.connections')
    def test_get_limit_details_with_restrictions(self, mock_connections):
        """Тест метода get_limit_details, є обмеження та статус 922."""
        mock_cursor = MagicMock()
        mock_connections['e_archive'].cursor.return_value.__enter__.return_value = mock_cursor

        # Емуляція даних
        mock_cursor.fetchall.return_value = [(1,), (2,), (3,)]
        mock_cursor.fetchone.side_effect = [(922,)]

        app_number = 'a202400001'
        obj_type_id = 1

        result = self.service.get_limit_details(app_number, obj_type_id)

        expected_result = (922, {1, 2, 3})
        self.assertEqual(result, expected_result)
