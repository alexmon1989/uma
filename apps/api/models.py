from django.db import models
from apps.search.models import IpcAppList, ObjType


class OpenData(models.Model):
    """Модель для открытых данных."""
    app = models.ForeignKey(IpcAppList, on_delete=models.CASCADE, verbose_name='Заявка')
    data = models.TextField(verbose_name='Дані у форматі JSON', default=None, null=True, blank=True)
    data_docs = models.TextField(verbose_name='Стан діловодства у форматі JSON', default=None, null=True, blank=True)
    data_payments = models.TextField(
        verbose_name='Платежі, збори',
        default=None,
        null=True,
        blank=True
    )
    # Поля для денормализации данных с целью ускорения поиска
    obj_type = models.ForeignKey(ObjType, blank=True, null=True, on_delete=models.CASCADE, default=None)
    obj_state = models.PositiveSmallIntegerField(default=2)
    last_update = models.DateTimeField(blank=True, null=True, default=None, db_index=True)
    app_number = models.CharField(max_length=100, blank=True, null=True, default=None)
    app_date = models.DateTimeField(blank=True, null=True, default=None, db_index=True)
    registration_number = models.CharField(blank=True, null=True, default=None, max_length=32)
    registration_date = models.DateTimeField(blank=True, null=True, default=None, db_index=True)
    files_path = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        verbose_name = 'Відкриті дані'
        verbose_name_plural = 'Відкриті дані'


class Person(models.Model):
    person_name = models.CharField('Найменування особи', max_length=1024)
    open_data = models.ForeignKey(OpenData, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Особа'
        verbose_name_plural = 'Особи'
