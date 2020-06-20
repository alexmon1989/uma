from django.db import models
from apps.search.models import IpcAppList, ObjType


class OpenData(models.Model):
    """Модель для открытых данных."""
    app = models.ForeignKey(IpcAppList, on_delete=models.CASCADE, verbose_name='Заявка')
    data = models.TextField(verbose_name='Дані у форматі JSON')
    # Поля для денормализации данных с целью ускорения поиска
    obj_type = models.ForeignKey(ObjType, blank=True, null=True, on_delete=models.CASCADE, default=None)
    obj_state = models.PositiveSmallIntegerField(default=2, db_index=True)
    last_update = models.DateTimeField(blank=True, null=True, default=None, db_index=True)
    app_number = models.CharField(max_length=100, blank=True, null=True, default=None, db_index=True)
    app_date = models.DateTimeField(blank=True, null=True, default=None, db_index=True)
    registration_number = models.CharField(blank=True, null=True, default=None, db_index=True, max_length=32)
    registration_date = models.DateTimeField(blank=True, null=True, default=None, db_index=True)

    class Meta:
        verbose_name = 'Відкриті дані'
        verbose_name_plural = 'Відкриті дані'
