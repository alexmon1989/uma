from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from uma.abstract_models import TimeStampedModel
from ckeditor_uploader.fields import RichTextUploadingField
from annoying.fields import AutoOneToOneField
from ..search.models import IpcAppList


class License(TimeStampedModel):
    """Модель для управления текстом текущей лицензии."""
    text = RichTextUploadingField('Текст')
    users = models.ManyToManyField(get_user_model())

    class Meta:
        verbose_name = 'Текст ліцензії'
        verbose_name_plural = 'Текст ліцензії'


class Balance(models.Model):
    """Модель для хранения значения количества денег на счету пользователя."""
    value = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Значення', default=0)
    user = AutoOneToOneField(get_user_model(), primary_key=True, verbose_name='Користувач', on_delete=models.CASCADE)

    def __str__(self):
        return f"Баланс рахунку користувача {self.user.get_username_full()}"

    class Meta:
        verbose_name = 'Баланс рахунку'
        verbose_name_plural = 'Баланси рахунків'


OPERATIONS_TYPES = (
    (1, _('Надання доступу до інформації про заявку')),
    (2, _('Поповнення рахунку')),
)


class BalanceOperation(TimeStampedModel):
    """Модель операции со счётом пользователя."""
    balance = models.ForeignKey(Balance, on_delete=models.CASCADE, verbose_name='Рахунок')
    value = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Значення', default=0)
    type = models.IntegerField('Тип операції', choices=OPERATIONS_TYPES)
    app = models.ForeignKey(IpcAppList, on_delete=models.CASCADE, verbose_name='Заявка', null=True, blank=True)

    class Meta:
        verbose_name = 'Операція з балансом рахунку'
        verbose_name_plural = 'Операції з балансом рахунків'
