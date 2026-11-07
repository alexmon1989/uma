from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from .services import OriginalDocumentService


class OriginalDocumentViewTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.page_url = reverse('services:original_document')
        self.task_url = reverse('generate_original_document')

    def test_get_page_ensures_csrf_cookie(self):
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', response.cookies)
        # Verify no recaptcha in context
        self.assertNotIn('site_key', response.context)
        self.assertNotIn('RECAPTCHA_ENABLED', response.context)

    def test_get_task_endpoint_method_not_allowed(self):
        # generate_original_document only allows POST
        response = self.client.get(self.task_url)
        self.assertEqual(response.status_code, 405)

    def test_post_without_csrf_token_forbidden(self):
        response = self.client.post(self.task_url, {'sec_code': '1234567890'})
        self.assertEqual(response.status_code, 403)

    @patch('apps.services.views.get_original_document.delay')
    def test_post_with_valid_sec_codes(self, mock_delay):
        mock_task = MagicMock()
        mock_task.id = 'dummy-task-id'
        mock_delay.return_value = mock_task

        valid_codes = [
            '1234567890',
            'CR1234567890',
            'cr1234567890',
            'Cr1234567890',
            '  CR1234567890  ',
        ]

        # First obtain CSRF cookie
        self.client.get(self.page_url)

        for code in valid_codes:
            response = self.client.post(self.task_url, {'sec_code': code}, follow=True)
            self.assertEqual(response.status_code, 200, f"Failed for code: {code}")
            data = response.json()
            self.assertEqual(data.get('task_id'), 'dummy-task-id')

    def test_post_with_invalid_sec_codes(self):
        # First obtain CSRF cookie
        self.client.get(self.page_url)

        invalid_codes = [
            '',
            '123',
            '12345678901',
            'ABC1234567890',
            'CR12345',
            'CR12345678901',
            '../../etc/passwd',
            'CR123456789a',
        ]

        for code in invalid_codes:
            response = self.client.post(self.task_url, {'sec_code': code}, follow=True)
            self.assertEqual(response.status_code, 400, f"Expected 400 for code: {code}")
            self.assertEqual(response.json().get('error'), 'Довжина ідентифікатора документу невірна')


class OriginalDocumentServiceTests(TestCase):
    @patch('apps.services.services.connections')
    @patch('apps.services.services.settings')
    def test_service_generates_uuid_filename(self, mock_settings, mock_connections):
        import tempfile
        import os
        import re

        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings.MEDIA_ROOT = temp_dir
            mock_settings.MEDIA_URL = '/media/'

            mock_cursor = MagicMock()
            # Return one row: (row_id, filename, content)
            mock_cursor.fetchall.return_value = [(1, 'test.pdf', b'fake-content')]
            mock_cursor.nextset.return_value = False
            mock_connections.__getitem__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

            service = OriginalDocumentService('CR1234567890')
            result_url = service.create_original_document_archive()

            self.assertTrue(result_url.startswith('/media/original_documents/'))
            filename = os.path.basename(result_url)
            # Must be UUID4 format + .zip
            self.assertTrue(re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.zip$', filename))

            # Verify file exists on disk
            full_path = os.path.join(temp_dir, 'original_documents', filename)
            self.assertTrue(os.path.exists(full_path))
