from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField


class ContactsPage(models.Model):
    """Модель для страницы 'Про сервіс'"""
    title_uk = models.CharField('Заголовок сторінки (укр.)', max_length=255, default='Контакти')
    title_en = models.CharField('Заголовок сторінки (en.)', max_length=255, default='Contacts')
    content_uk = RichTextUploadingField('Зміст (укр.)', blank=True, null=True)
    content_en = RichTextUploadingField('Зміст (en.)', blank=True, null=True)

    content_sidebar_uk = RichTextUploadingField('Зміст бокової панелі (укр.)', blank=True, null=True)
    content_sidebar_en = RichTextUploadingField('Зміст бокової панелі (en.)', blank=True, null=True)

    admin_email_1 = models.EmailField('Email адміністратора (для відображення) 1', blank=True, null=True)
    admin_email_2 = models.EmailField('Email адміністратора (для відображення) 2', blank=True, null=True)
    admin_email_3 = models.EmailField('Email адміністратора (для відображення) 3', blank=True, null=True)
    admin_phone_1 = models.CharField('Телефон адміністратора 1', max_length=255, blank=True, null=True)
    admin_phone_2 = models.CharField('Телефон адміністратора 2', max_length=255, blank=True, null=True)
    admin_phone_3 = models.CharField('Телефон адміністратора 3', max_length=255, blank=True, null=True)

    consultations_phone_1 = models.CharField('Телефон консультанта з заявниками 1', max_length=255, blank=True, null=True)
    consultations_phone_2 = models.CharField('Телефон консультанта з заявниками 2', max_length=255, blank=True, null=True)
    consultations_phone_3 = models.CharField('Телефон консультанта з заявниками 3', max_length=255, blank=True, null=True)
    consultations_phone_4 = models.CharField('Телефон консультанта з заявниками 4', max_length=255, blank=True, null=True)

    operating_mode_uk = models.CharField('Режим роботи (укр.)', max_length=255, blank=True, null=True)
    operating_mode_en = models.CharField('Режим роботи (en.)', max_length=255, blank=True, null=True)
    lunch_break_uk = models.CharField('Перерва (укр.)', max_length=255, blank=True, null=True)
    lunch_break_en = models.CharField('Перерва (en.)', max_length=255, blank=True, null=True)

    fb_url = models.URLField('Посилання на Facebook', blank=True, null=True)
    youtube_url = models.URLField('Посилання на Youtube', blank=True, null=True)
    twitter_url = models.URLField('Посилання на Twitter', blank=True, null=True)
    instagram_url = models.URLField('Посилання на Instagram', blank=True, null=True)

    form_email_1 = models.EmailField('Email форми 1', blank=True, null=True)
    form_email_2 = models.EmailField('Email форми 2', blank=True, null=True)
    form_email_3 = models.EmailField('Email форми 3', blank=True, null=True)

    def __str__(self):
        return self.title_uk

    class Meta:
        verbose_name = 'Зміст сторінки'
        verbose_name_plural = 'Зміст сторінки'
