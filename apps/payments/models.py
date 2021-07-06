from django.db import models
from django.utils.translation import get_language
from ckeditor_uploader.fields import RichTextUploadingField
from ..search.models import ObjType
from uma.abstract_models import TimeStampedModel


class ServiceGroup(models.Model):
    """Модель платёжной группы услуг."""
    code = models.CharField('Код платіжної групи', max_length=16)
    title = models.CharField('Назва', max_length=255)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Платіжна група послуги'
        verbose_name_plural = 'Платіжні групи послуг'


OBJ_STATE_CHOICES = (
    (1, 'Заявка'),
    (2, 'Охоронний документ')
)


class Group(models.Model):
    """Модель группы сборов."""
    title_uk = models.CharField('Назва групи (укр.)', max_length=255)
    title_en = models.CharField('Назва групи (eng.)', max_length=255, default='', blank=True, null=True)
    obj_types = models.ManyToManyField(ObjType, verbose_name="Типи об'єктів", blank=True)
    obj_state = models.PositiveSmallIntegerField("Стан об'єкта", choices=OBJ_STATE_CHOICES, null=True, blank=True)
    weight = models.IntegerField("Вага", default=999, help_text='Чим більше вага, тим вище елемент у списку')

    def __str__(self):
        return self.title_uk

    def get_obj_types(self):
        return ", ".join([o.obj_type_ua for o in self.obj_types.all()])

    @property
    def group_title(self):
        if get_language() == 'uk':
            return self.title_uk
        return self.title_en or self.title_uk

    class Meta:
        verbose_name = 'Група сборів'
        verbose_name_plural = 'Групи сборів'
        ordering = ('-weight',)


class FeeType(models.Model):
    """Модель типа сбора."""
    title_uk = models.CharField('Назва збору (укр.)', max_length=1024)
    title_en = models.CharField('Назва збору (eng.)', max_length=1024, default='', blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Група сбору')
    service_group = models.ForeignKey(ServiceGroup, on_delete=models.SET_NULL, null=True)
    code = models.CharField('Код сбору', max_length=255)
    needs_app_number = models.BooleanField('Потребує номера заявки', default=True)

    def __str__(self):
        return self.title_uk

    @property
    def code_title(self):
        if get_language() == 'en' and self.title_en:
            return f"{self.code} - {self.title_en}"
        return f"{self.code} - {self.title_uk}"

    class Meta:
        verbose_name = 'Вид сбору'
        verbose_name_plural = 'Види сборів'


class Order(TimeStampedModel):
    """Модель заказа."""
    fee_type = models.ForeignKey('FeeType', on_delete=models.SET_NULL, default=None, blank=False, null=True,
                                 verbose_name='Вид сбору')
    app_number = models.CharField('Номер заявки', max_length=32, blank=True, null=True)
    value = models.PositiveIntegerField('Сума платежу')

    @property
    def is_paid(self):
        return self.orderoperation_set.all().filter(code=1).exists()

    def __str__(self):
        return f"Заявка {self.app_number}, збір {self.fee_type.title_uk}"

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'


ORDER_OPERATION_CODE_CHOICES = (
    (1, 'Успішно сплачено'),
    (2, 'Помилка при сплаті')
)


class OrderOperation(TimeStampedModel):
    """Модель операции с заказом."""
    order = models.ForeignKey('Order', on_delete=models.CASCADE, verbose_name='Замовлення')
    code = models.SmallIntegerField('Код операції', help_text='1 - успішно сплачено, 2 - помилка при сплаті',
                                    choices=ORDER_OPERATION_CODE_CHOICES)
    value = models.PositiveIntegerField('Сума платежу', default=None, blank=True, null=True)
    pay_request_pb_xml = models.TextField('Запит PrivatBank24', default=None, blank=True, null=True)

    def __str__(self):
        return f"{self.code}, {self.order}"

    class Meta:
        verbose_name = 'Операція по замовленню'
        verbose_name_plural = 'Операції по замовленням'


class Page(TimeStampedModel):
    """Модель страницы формирования заказа."""
    description_uk = RichTextUploadingField('Опис сторінки (укр.)', blank=True)
    description_en = RichTextUploadingField('Опис сторінки (англ.)', blank=True)

    @property
    def description(self):
        if get_language() == 'uk':
            return self.description_uk
        return self.description_en or self.description_uk

    def __str__(self):
        return 'Інформація на сторінці формування замовлення'

    class Meta:
        verbose_name = 'Інформація на сторінці формування замовлення'
        verbose_name_plural = 'Інформація на сторінці формування замовлення'
