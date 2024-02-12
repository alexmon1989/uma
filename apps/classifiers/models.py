from django.db import models
from apps.search.models import ObjType

from uma.abstract_models import TimeStampedModel


class DocumentTypeNacp(TimeStampedModel):
    """Модель типов документов, доступных для скачивания представителями НАЗК."""
    title = models.CharField('Тип документа', max_length=512)
    obj_types = models.ManyToManyField(ObjType, verbose_name='Тип об\'єкта')
    enabled = models.BooleanField(
        default=False,
        verbose_name='Дозволено для завантаження',
        help_text='Незалежно від значення поля, '
                  'представники НАЗК зможуть завантажувати документи лише опублікованих ОПВ'
    )

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = 'Тип документа (НАЗК)'
        verbose_name_plural = 'Типи документів (НАЗК)'
        db_table = 'cl_document_types_nacp'
