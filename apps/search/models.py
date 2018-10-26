from django.db import models


class ObjType(models.Model):
    """Модель типа объекта ИС."""
    id = models.AutoField(db_column='idObjType', primary_key=True)
    obj_type_ua = models.CharField(db_column='ObjTypeUA', max_length=100)
    obj_type_en = models.CharField(db_column='ObjTypeEN', max_length=100)
    obj_server_folder = models.CharField(db_column='ObjServerFolder', max_length=255, blank=True, null=True)
    file_server_name = models.CharField(db_column='FileServerName', max_length=250, blank=True, null=True)
    net_share_name = models.CharField(db_column='NetShareName', max_length=500, blank=True, null=True)

    def __str__(self):
        return self.obj_type_ua

    class Meta:
        managed = False
        db_table = 'cl_IP_ObjTypes'


class IpcCode(models.Model):
    """Модель кода ИНИД"""
    id = models.AutoField(db_column='idIPCCode', primary_key=True)
    obj_type = models.ForeignKey(ObjType, models.DO_NOTHING, db_column='idObjType', verbose_name="Тип об'єкта")
    code_value_ua = models.CharField(db_column='CodeValueUA', max_length=300, verbose_name='Назва (укр.)')
    code_value_en = models.CharField(db_column='CodeValueEN', max_length=300, verbose_name='Назва (англ.)', blank=True,
                                     null=True)
    code_data_type = models.CharField(db_column='CodeDataType', max_length=32, blank=True, null=True)
    code_xml_struct = models.CharField(db_column='CodeXMLStruct', max_length=50, blank=True, null=True)
    code_inid = models.CharField(db_column='CodeINID', max_length=20, blank=True, null=True,
                                 verbose_name='Значення коду ІНІД')

    def __str__(self):
        return f"{self.code_value_ua} ({self.obj_type.obj_type_ua})"

    class Meta:
        managed = False
        db_table = 'cl_IPCCodes'
        verbose_name = 'Код ІНІД'
        verbose_name_plural = 'Коди ІНІД'
        ordering = ('code_inid',)


class ScheduleType(models.Model):
    """Модель реестра ОПС."""
    id = models.AutoField(db_column='idSheduleType', primary_key=True)
    schedule_type = models.CharField(db_column='SheduleType', max_length=300)
    obj_type = models.ForeignKey(ObjType, models.DO_NOTHING, db_column='idObjType')
    run_app_name = models.CharField(db_column='RunAppName', max_length=100, blank=True, null=True)
    run_app_path = models.CharField(db_column='RunAppPath', max_length=200, blank=True, null=True)
    is_scheduled = models.IntegerField(db_column='isSheduled', blank=True, null=True)
    mask_task_name = models.CharField(db_column='MaskTaskName', max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cl_SheduleTypes'


class InidCodeSchedule(models.Model):
    """Промежуточная модель, описывающая свзяь многие-ко-многим между моделями ScheduleType и IpcCode."""
    id = models.AutoField(db_column='idLink', primary_key=True)
    schedule_type = models.ForeignKey(ScheduleType, models.DO_NOTHING, db_column='idSheduleType', blank=True, null=True)
    ipc_code = models.ForeignKey(IpcCode, models.DO_NOTHING, db_column='idIPCCode', blank=True, null=True)
    enable_search = models.IntegerField(db_column='EnableSearch', blank=True, null=True)
    enable_view = models.IntegerField(db_column='EnableView', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cl_LinkShedule_INID_Codes'


FIELD_TYPE_CHOICES = (
    ('integer', 'Integer'),
    ('keyword', 'Keyword'),
    ('text', 'Text'),
    ('date', 'Date'),
    ('nested', 'Nested'),
)


class ElasticIndexField(models.Model):
    """Модель для описания индекса ElasticSearch."""
    field_name = models.CharField('Назва поля у індексі ElasticSearch', max_length=255)
    field_type = models.CharField('Тип поля ElasticSearch', max_length=255, choices=sorted(FIELD_TYPE_CHOICES))
    parent = models.ForeignKey('self', verbose_name='Батьківське поле (nested)', on_delete=models.SET_NULL, null=True,
                               blank=True, limit_choices_to={'field_type': 'nested'})
    ipc_codes = models.ManyToManyField(IpcCode, verbose_name='ІНІД-коди', blank=True)

    def __str__(self):
        return self.field_name

    class Meta:
        verbose_name = 'Поле ElasticSearch'
        verbose_name_plural = 'Індекс ElasticSearch'
        ordering = ('field_name',)


class SimpleSearchField(models.Model):
    """Модель для описания формы простого поиска."""
    field_label_ua = models.CharField('Label поля (укр.)', max_length=255, default='')
    field_label_en = models.CharField('Label поля (англ.)', max_length=255, default='')
    field_name = models.CharField('Name поля', max_length=255)
    is_visible = models.BooleanField('Відображати', default=True)
    elastic_index_fields = models.ManyToManyField(ElasticIndexField, verbose_name='Поля ElasticSearch', blank=True,
                                                  limit_choices_to={'field_type__in': ('integer', 'keyword', 'text', 'date')})

    def __str__(self):
        return self.field_name

    class Meta:
        verbose_name = 'Поле форми пошуку'
        verbose_name_plural = 'Проста форма пошуку'
        ordering = ('field_name',)
