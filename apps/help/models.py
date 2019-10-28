from django.db import models
from uma.abstract_models import TimeStampedModel
from ckeditor_uploader.fields import RichTextUploadingField


class Help(TimeStampedModel):
    """Модель для страницы 'Про сервіс'"""
    title_uk = models.CharField('Заголовок укр.', max_length=255, default='Допомога')
    content_uk = RichTextUploadingField('Зміст укр.', blank=True)
    title_en = models.CharField('Заголовок англ.', max_length=255, default='Help')
    content_en = RichTextUploadingField('Зміст англ.', blank=True)

    def __str__(self):
        return self.title_uk

    class Meta:
        verbose_name = 'Зміст сторінки'
        verbose_name_plural = 'Зміст сторінки'


class Section(TimeStampedModel):
    """Модель раздела помощи."""
    title_uk = models.CharField('Заголовок укр.', max_length=255)
    title_en = models.CharField('Заголовок англ.', max_length=255, blank=True)
    slug = models.SlugField(verbose_name='Ідентифікатор для URL')
    weight = models.PositiveIntegerField(
        'Вага',
        default=1000,
        help_text='Чим більша вага, тим вище на сторінці цей розділ'
    )
    is_enabled = models.BooleanField('Відображати', default=True)

    def __str__(self):
        return self.title_uk

    class Meta:
        verbose_name = 'Розділ'
        verbose_name_plural = 'Розділи'


class Question(TimeStampedModel):
    """Модель вопроса"""
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text='Питання без розділу не відображаються',
        verbose_name='Розділ'
    )
    title_uk = models.CharField('Заголовок укр.', max_length=255)
    content_uk = RichTextUploadingField('Зміст укр.', blank=True)
    title_en = models.CharField('Заголовок англ.', max_length=255, blank=True)
    content_en = RichTextUploadingField('Зміст англ.', blank=True)
    slug = models.SlugField(verbose_name='Ідентифікатор для URL')
    weight = models.PositiveIntegerField(
        'Вага',
        default=1000,
        help_text='Чим більша вага, тим вище на сторінці це питання'
    )
    is_enabled = models.BooleanField('Відображати', default=True)

    def __str__(self):
        return self.title_uk

    class Meta:
        verbose_name = 'Питання'
        verbose_name_plural = 'Питання'
