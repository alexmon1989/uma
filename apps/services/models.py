from django.conf import settings
from django.db import models
from uma.abstract_models import TimeStampedModel
from ckeditor_uploader.fields import RichTextUploadingField


class APIDescription(TimeStampedModel):
    """Модель для страницы 'API'"""
    title_uk = models.CharField('Заголовок', max_length=255, default='API')
    content_uk = RichTextUploadingField('Зміст', blank=True)
    title_en = models.CharField('Заголовок', max_length=255, default='API')
    content_en = RichTextUploadingField('Зміст', blank=True)

    def __str__(self):
        return self.title_uk

    class Meta:
        verbose_name = 'Зміст сторінки "API"'
        verbose_name_plural = 'Зміст сторінки "API"'


class OriginalDocumentDownloadLog(TimeStampedModel):
    """Журнал успішних отримань (формувань) оригіналів документів з Є-Архіву."""
    sec_code = models.CharField(
        'Ідентифікатор документа',
        max_length=50,
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Користувач'
    )
    ip_address = models.GenericIPAddressField(
        'IP-адреса',
        null=True,
        blank=True
    )
    user_agent = models.CharField(
        'User-Agent',
        max_length=500,
        blank=True
    )
    file_path = models.CharField(
        'Шлях до сформованого файлу',
        max_length=255,
        blank=True
    )

    class Meta:
        verbose_name = 'Лог отримання оригіналу документа'
        verbose_name_plural = 'Логи отримання оригіналів документів'
        db_table = 'services_original_document_download_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        user_repr = self.user.get_username() if self.user else (self.ip_address or 'Anonymous')
        return f"{self.sec_code} ({user_repr}) - {self.created_at:%Y-%m-%d %H:%M:%S}"
