from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from .models import OriginalDocumentDownloadLog
from .services import OriginalDocumentService, original_document_download_log_create
from .tasks import get_original_document

User = get_user_model()


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

    @patch('apps.services.views.get_original_document.delay')
    def test_post_passes_user_ip_and_user_agent_to_task(self, mock_delay):
        mock_task = MagicMock()
        mock_task.id = 'dummy-task-id'
        mock_delay.return_value = mock_task

        user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_login(user)

        self.client.get(self.page_url)
        response = self.client.post(
            self.task_url,
            {'sec_code': '1234567890'},
            HTTP_USER_AGENT='CustomAgent/1.0',
            REMOTE_ADDR='192.168.1.100',
        )
        self.assertEqual(response.status_code, 200)

        mock_delay.assert_called_once_with(
            '1234567890',
            user_id=user.pk,
            ip='192.168.1.100',
            user_agent='CustomAgent/1.0',
        )


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


class OriginalDocumentDownloadLogServiceTests(TestCase):
    def test_original_document_download_log_create(self):
        user = User.objects.create_user(username='loguser', password='password123')
        log = original_document_download_log_create(
            sec_code='CR1234567890',
            user_id=user.pk,
            ip_address='10.0.0.1',
            user_agent='TestBrowser',
            file_path='/media/original_documents/abc.zip',
        )
        self.assertEqual(log.sec_code, 'CR1234567890')
        self.assertEqual(log.user, user)
        self.assertEqual(log.ip_address, '10.0.0.1')
        self.assertEqual(log.user_agent, 'TestBrowser')
        self.assertEqual(log.file_path, '/media/original_documents/abc.zip')
        self.assertIn('CR1234567890', str(log))
        self.assertIn('loguser', str(log))


class GetOriginalDocumentTaskTests(TestCase):
    @patch.object(OriginalDocumentService, 'create_original_document_archive')
    def test_task_creates_log_on_success(self, mock_create_archive):
        mock_create_archive.return_value = '/media/original_documents/123.zip'
        user = User.objects.create_user(username='taskuser', password='password123')

        result = get_original_document(
            'CR1234567890',
            user_id=user.pk,
            ip='172.16.0.5',
            user_agent='TaskAgent/2.0',
        )

        self.assertEqual(result, '/media/original_documents/123.zip')
        self.assertEqual(OriginalDocumentDownloadLog.objects.count(), 1)
        log = OriginalDocumentDownloadLog.objects.first()
        self.assertEqual(log.sec_code, 'CR1234567890')
        self.assertEqual(log.user, user)
        self.assertEqual(log.ip_address, '172.16.0.5')
        self.assertEqual(log.user_agent, 'TaskAgent/2.0')
        self.assertEqual(log.file_path, '/media/original_documents/123.zip')

    @patch.object(OriginalDocumentService, 'create_original_document_archive')
    def test_task_does_not_create_log_when_not_found(self, mock_create_archive):
        mock_create_archive.return_value = ''

        result = get_original_document('CR1234567890', ip='1.1.1.1')

        self.assertEqual(result, '')
        self.assertEqual(OriginalDocumentDownloadLog.objects.count(), 0)
