from django.db import models
from uma.abstract_models import TimeStampedModel
from ckeditor_uploader.fields import RichTextUploadingField


class About(TimeStampedModel):
    """Модель для страницы 'Про сервіс'"""
    title_uk = models.CharField('Заголовок', max_length=255, default='Про сервіс')
    content_uk = RichTextUploadingField('Зміст', blank=True)
    title_en = models.CharField('Заголовок', max_length=255, default='About')
    content_en = RichTextUploadingField('Зміст', blank=True)

    def __str__(self):
        return self.title_uk

    class Meta:
        verbose_name = 'Зміст сторінки'
        verbose_name_plural = 'Зміст сторінки'
