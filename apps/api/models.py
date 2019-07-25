from django.db import models
from apps.search.models import IpcAppList


class OpenData(models.Model):
    """Модель для открытых данных."""
    app = models.ForeignKey(IpcAppList, on_delete=models.CASCADE, verbose_name='Заявка')
    data = models.TextField(verbose_name='Дані у форматі JSON')

    def __str__(self):
        return self.app.app_number

    class Meta:
        verbose_name = 'Відкриті дані'
        verbose_name_plural = 'Відкриті дані'
