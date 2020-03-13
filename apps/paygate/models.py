from django.db import models
from django.contrib.auth import get_user_model
from uma.abstract_models import TimeStampedModel


class Payment(TimeStampedModel):
    """Модель платежа ПриватБанка."""
    value = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Сума до оплати')
    value_paid = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Сума сплачена', null=True,
                                     blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    paid = models.BooleanField('Оплачено', default=False)
    pay_request_pb_xml = models.TextField('XML запиту ПБ після запису платежа', null=True, blank=True)

    def __str__(self):
        return str(self.value)

    class Meta:
        verbose_name = 'Платіж'
        verbose_name_plural = 'Платежі'
