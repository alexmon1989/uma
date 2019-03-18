from django.db import models
from uma.abstract_models import TimeStampedModel
from ckeditor_uploader.fields import RichTextUploadingField


class Help(TimeStampedModel):
    """Модель для страницы 'Про сервіс'"""
    title = models.CharField('Заголовок', max_length=255, default='Допомога')
    content = RichTextUploadingField('Зміст', blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Зміст сторінки'
        verbose_name_plural = 'Зміст сторінки'
