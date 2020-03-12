from django.db import models
from django.contrib.auth import get_user_model
from uma.abstract_models import TimeStampedModel


class Payment(TimeStampedModel):
    """Модель платежа ПриватБанка."""
    value = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Сума')
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    paid = models.BooleanField('Оплачено', default=False)

    def __str__(self):
        return str(self.value)

    class Meta:
        verbose_name = 'Платіж'
        verbose_name_plural = 'Платежі'
