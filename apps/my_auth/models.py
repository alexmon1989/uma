import random
import string
from django.db import models
from django.contrib.auth.models import User
from uma.abstract_models import TimeStampedModel


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


class KeyCenter(TimeStampedModel):
    """Модель данных центра сертификации ключей."""
    title = models.CharField('Назва', max_length=255)
    address = models.CharField('Web-адреса', max_length=255, blank=True, null=True)
    ocspAccessPointAddress = models.CharField('OCSP-сервер', max_length=255, blank=True, null=True)
    ocspAccessPointPort = models.PositiveIntegerField('Порт OCSP-сервера', blank=True, null=True)
    cmpAddress = models.CharField('CMP-сервер', max_length=255, blank=True, null=True)
    tspAddress = models.CharField('TSP-сервер', max_length=255, blank=True, null=True)
    tspAddressPort = models.PositiveIntegerField('Порт TSP-сервера', blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'АЦСК'
        verbose_name_plural = 'АЦСК'
        ordering = ('title',)


def is_vip(self):
    """Возвращает значение (boolean) того является ли юзер суперадмином или членом группы 'Посадовці (чиновники)'"""
    return self.is_superuser or self.groups.filter(name='Посадовці (чиновники)').exists()

def get_username_short(self):
    if hasattr(self, 'certificateowner'):
        return self.certificateowner.pszSubjFullName
    return self.username


def get_username_full(self):
    if hasattr(self, 'certificateowner'):
        return self.certificateowner.pszSubjFullName
    return self.get_full_name()

User.add_to_class('is_vip', is_vip)
User.add_to_class('get_username_short', get_username_short)
User.add_to_class('get_username_full', get_username_full)
