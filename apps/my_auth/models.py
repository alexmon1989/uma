import random
import string
from django.db import models
from django.contrib.auth.models import User
from uma.abstract_models import TimeStampedModel


class PatentAttorney(TimeStampedModel):
    """Модель патентного поверенного."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Користувач')
    name = models.CharField('ПІБ особи', max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Патентний повірений'
        verbose_name_plural = 'Патентні повірені'


class CertificateOwner(TimeStampedModel):
    """Модель данных владельца сертификата ЭЦП."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Користувач')
    pszIssuer = models.CharField('Ім’я ЦСК, що видав сертифікат', max_length=255, blank=True, null=True)
    pszIssuerCN = models.CharField('Реквізити ЦСК, що видав сертифікат', max_length=255, blank=True, null=True)
    pszSerial = models.CharField('Реєстраційний номер сертифіката', max_length=255, blank=True, null=True)
    pszSubject = models.CharField('Ім’я власника сертифіката', max_length=255, blank=True, null=True)
    pszSubjCN = models.CharField('Реквізити власника сертифіката', max_length=255, blank=True, null=True)
    pszSubjOrg = models.CharField('Організація до якої належить власник сертифіката', max_length=255, blank=True,
                                  null=True)
    pszSubjOrgUnit = models.CharField('Підрозділ організації до якої належить власник сертифіката', max_length=255,
                                      blank=True, null=True)
    pszSubjTitle = models.CharField('Посада власника сертифіката', max_length=255, blank=True, null=True)
    pszSubjState = models.CharField('Назва області до якої належить власник сертифіката', max_length=255, blank=True,
                                    null=True)
    pszSubjFullName = models.CharField('Повне ім’я власника сертифіката', max_length=255, blank=True, null=True)
    pszSubjAddress = models.CharField('Адреса власника сертифіката', max_length=255, blank=True, null=True)
    pszSubjPhone = models.CharField('Номер телефону власника сертифіката', max_length=255, blank=True, null=True)
    pszSubjEMail = models.CharField('Адреса електронної пошти власника сертифіката', max_length=255, blank=True,
                                    null=True)
    pszSubjDNS = models.CharField('DNS-ім`я чи інше технічного засобу', max_length=255, blank=True, null=True)
    pszSubjEDRPOUCode = models.CharField('Код ЄДРПОУ власника сертифіката', max_length=255, blank=True, null=True)
    pszSubjDRFOCode = models.CharField('Код ДРФО власника сертифіката', max_length=255, blank=True, null=True)
    pszSubjLocality = models.CharField('Locality власника сертифіката', max_length=255, blank=True, null=True)

    def __str__(self):
        return self.pszSerial

    def save(self, *args, **kwargs):
        """Переопределение метода сохранения модели."""
        super().save(*args, **kwargs)
        # Создание нового пользователя
        if not self.user:
            user, created = User.objects.get_or_create(username=self.pszSerial, email=self.pszSubjEMail)
            if not created:
                user.set_password(''.join(random.choices(string.ascii_uppercase + string.digits, k=8)))
            self.user = user
            self.save()

    class Meta:
        verbose_name = 'Сертифікат'
        verbose_name_plural = 'Сертифікати'


def is_vip(self):
    """Возвращает значение (boolean) того является ли юзер суперадмином или членом группы 'Посадовці (чиновники)'"""
    return self.is_superuser or self.groups.filter(name='Посадовці (чиновники)').exists()


def is_patent_attorney(self):
    """Возвращает значение (boolean) того является ли юзер членом группы 'Патентні повірен'"""
    return self.groups.filter(name='Патентні повірені').exists()


def get_username_short(self):
    if hasattr(self, 'certificateowner'):
        return self.certificateowner.pszSubjFullName
    return self.username


def get_username_full(self):
    if hasattr(self, 'certificateowner'):
        return self.certificateowner.pszSubjFullName
    return self.get_full_name()


def get_email(self):
    """Возвращает эл. адр. пользователя."""
    if self.email:
        return self.email
    if hasattr(self, 'certificateowner'):
        return self.certificateowner.pszSubjEMail
    return ''


def user_str(self):
    full_name = self.get_username_full()
    if full_name.strip():
        return f"{full_name} (дата реєстрації: {self.date_joined.strftime('%d.%m.%Y %H:%M:%S')})"
    return self.username


User.add_to_class('__str__', user_str)
User.add_to_class('is_vip', is_vip)
User.add_to_class('is_patent_attorney', is_patent_attorney)
User.add_to_class('get_username_short', get_username_short)
User.add_to_class('get_username_full', get_username_full)
User.add_to_class('get_email', get_email)
