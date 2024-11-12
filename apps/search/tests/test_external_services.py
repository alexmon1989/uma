from django.test import TestCase
from unittest.mock import patch, MagicMock

from apps.search.services.external import gloc_get_sanctioned_objects


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
