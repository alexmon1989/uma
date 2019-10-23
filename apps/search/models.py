from django.db import models
from django.contrib.auth.models import User
from ckeditor_uploader.fields import RichTextUploadingField


class IpcAppList(models.Model):
    id = models.AutoField(db_column='idAPPNumber', primary_key=True)
    app_number = models.CharField(db_column='APP_Number', max_length=100, blank=True, null=True)
    registration_number = models.IntegerField(db_column='RegistrationNumber', blank=True, null=True)
    registration_date = models.DateField(db_column='RegistrationDate', blank=True, null=True)
    id_shedule_type = models.IntegerField(db_column='idSheduleType')
    files_path = models.CharField(db_column='FilesPath', max_length=500, blank=True, null=True)
    id_parent = models.IntegerField(db_column='idParent', blank=True, null=True)
    id_claim = models.IntegerField(db_column='idClaim', blank=True, null=True)
    obj_type = models.ForeignKey('ObjType', db_column='idObjType', blank=True, null=True, on_delete=models.CASCADE)
    changescount = models.IntegerField(db_column='ChangesCount')
    lastupdate = models.DateField(db_column='LastUpdate', blank=True, null=True)
    idstatus = models.IntegerField(db_column='idStatus', blank=True, null=True)
    app_date = models.DateTimeField(db_column='APP_Date', blank=True, null=True)
    elasticindexed = models.IntegerField(db_column='ElasticIndexed', blank=True, null=True)
    notification_date = models.DateField(db_column='NotificationDate', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'IPC_AppList'


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

    def __str__(self):
        return self.schedule_type

    class Meta:
        managed = False
        db_table = 'cl_SheduleTypes'
        verbose_name = 'Реєстр'
        verbose_name_plural = 'Реєстри'


class InidCodeSchedule(models.Model):
    """Промежуточная модель, описывающая свзяь многие-ко-многим между моделями ScheduleType и IpcCode."""
    id = models.AutoField(db_column='idLink', primary_key=True)
    schedule_type = models.ForeignKey(ScheduleType, models.DO_NOTHING, db_column='idSheduleType', blank=True, null=True,
                                      verbose_name='Реєстр')
    ipc_code = models.ForeignKey(IpcCode, models.DO_NOTHING, db_column='idIPCCode', blank=True, null=True,
                                 verbose_name='Код ІНІД')
    elastic_index_field = models.ForeignKey('ElasticIndexField', db_column='ElasticIndexField',
                                            on_delete=models.SET_NULL, blank=True, null=True,
                                            verbose_name='Поле індексу ElasticSearch')
    enable_search = models.BooleanField(db_column='EnableSearch', blank=False, null=False,
                                        verbose_name='Дозволяти пошук', default=False)
    enable_view = models.BooleanField(db_column='EnableView', blank=False, null=False,
                                      verbose_name='Відображати параметр на сторінці об\'єкта')

    class Meta:
        managed = False
        db_table = 'cl_LinkShedule_INID_Codes'
        verbose_name = 'Пошуковий параметр'
        verbose_name_plural = 'Пошукові параметри'

    @staticmethod
    def get_ipc_codes_with_schedules(lang_code):
        """Возвращает ИНИД коды с реестрами, в оторый они входят"""
        ipc_codes = InidCodeSchedule.objects.exclude(ipc_code__isnull=True).filter(enable_search=True).order_by(
            f"ipc_code__code_value_{lang_code}"
        ).values(
            'ipc_code__id',
            f"ipc_code__code_value_{lang_code}",
            'ipc_code__obj_type__id',
            'schedule_type__id',
            'ipc_code__code_data_type',
            f"ipc_code__obj_type__obj_type_{lang_code}"
        )
        ipc_codes_result = {}
        for ipc_code in ipc_codes:
            if not ipc_codes_result.get(ipc_code['ipc_code__id']):
                ipc_codes_result[ipc_code['ipc_code__id']] = {
                    'id': ipc_code['ipc_code__id'],
                    'value': ipc_code[f"ipc_code__code_value_{lang_code}"],
                    'obj_type_id': ipc_code['ipc_code__obj_type__id'],
                    'obj_type': ipc_code[f"ipc_code__obj_type__obj_type_{lang_code}"],
                    'schedule_types': [ipc_code['schedule_type__id']],
                    'data_type': ipc_code['ipc_code__code_data_type'],
                }
            else:
                ipc_codes_result[ipc_code['ipc_code__id']]['schedule_types'].append(ipc_code['schedule_type__id'])
        return list(ipc_codes_result.values())


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
    is_visible = models.BooleanField('Відображати', default=True)
    elastic_index_field = models.ForeignKey('ElasticIndexField', db_column='ElasticIndexField',
                                            on_delete=models.SET_NULL, blank=True, null=True,
                                            verbose_name='Поле індексу ElasticSearch')
    weight = models.PositiveIntegerField(
        'Вага',
        default=1000,
        help_text='Чим більша вага, тим вище параметр пошуку у списку'
    )

    def __str__(self):
        return self.field_label_ua

    class Meta:
        verbose_name = 'Поле форми пошуку'
        verbose_name_plural = 'Проста форма пошуку'
        ordering = ('id',)


class AppDocuments(models.Model):
    """Модель документов заявки."""
    id = models.AutoField(db_column='idDocument', primary_key=True)
    enter_num = models.IntegerField(db_column='enterNum')
    app = models.ForeignKey('IpcAppList', models.DO_NOTHING, db_column='idAPPNumber')
    add_date = models.DateTimeField(db_column='AddDate')
    file_name = models.CharField(db_column='FileName', max_length=500, blank=True, null=True)
    file_type = models.CharField(db_column='FileType', max_length=10, blank=True, null=True)
    barcode = models.CharField(db_column='BarCODE', max_length=50, blank=True, null=True)
    cead_id_doc = models.IntegerField(db_column='CEADIdDoc', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'APP_Documents'

    @staticmethod
    def get_app_documents(id_app_number):
        """Возвращает словарь документов по номеру заявки."""
        objects = AppDocuments.objects.filter(
            app__id=id_app_number,
            enter_num__in=(98, 99, 100, 101),
            file_type='pdf'
        ).values()
        documents = {}
        for document in objects:
            # Формула
            if document['enter_num'] == 98:
                documents['cl'] = document
            # Описание
            elif document['enter_num'] == 99:
                documents['de'] = document
            # Описание
            elif document['enter_num'] == 101:
                documents['de_pub'] = document
            else:
                if 'A_UA' in document['file_name']:
                    # Реферат укр.
                    documents['ab_ua'] = document
                if 'A_RU' in document['file_name']:
                    # Реферат рос.
                    documents['ab_ru'] = document
                if 'A_EN' in document['file_name']:
                    # Реферат англ.
                    documents['ab_en'] = document
        return documents


class OrderService(models.Model):
    """Модель таблицы ls_OrderService."""
    id = models.AutoField(db_column='idOrder', primary_key=True)
    user = models.ForeignKey(User, db_column='idUser', on_delete=models.DO_NOTHING, blank=True, null=True)
    ip_user = models.GenericIPAddressField(db_column='IP_User', max_length=100, blank=True, null=True)
    order_completed = models.BooleanField(db_column='OrderCompleted', default=0)
    app = models.ForeignKey('IpcAppList', models.DO_NOTHING, db_column='idAPPNumber', blank=True, null=True)
    completion_datetime = models.DateTimeField(db_column='CompletionDateTime', blank=True, null=True)
    created_at = models.DateTimeField(db_column='CreateDateTime', auto_now_add=True)
    create_external_documents = models.IntegerField(default=0)
    externaldoc_enternum = models.IntegerField(db_column='externalDoc_EnterNUM', blank=True, null=True)
    external_doc_body = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ls_OrderService'


class OrderDocument(models.Model):
    """Модель таблицы ls_OrderDocuments."""
    id = models.AutoField(db_column='idOrderDoc', primary_key=True)
    order = models.ForeignKey('OrderService', models.DO_NOTHING, db_column='idOrder', blank=True, null=True)
    id_cead_doc = models.IntegerField(db_column='idCEADDoc', blank=True, null=True)
    file_type = models.CharField(db_column='FileType', max_length=20, blank=True, null=True)
    file_size = models.IntegerField(db_column='FileSize', blank=True, null=True)
    file_name = models.CharField(db_column='FileName', blank=True, null=True, max_length=600)

    class Meta:
        managed = False
        db_table = 'ls_OrderDocuments'


class IndexationError(models.Model):
    """Модель ошибки индексации."""
    app = models.ForeignKey('IpcAppList', models.CASCADE, db_column='idAPPNumber')
    type = models.CharField(blank=True, null=True, max_length=255)
    json_path = models.CharField(blank=True, null=True, max_length=255)
    text = models.TextField(blank=True, null=True)
    indexation_process = models.ForeignKey('IndexationProcess', on_delete=models.CASCADE, blank=True, null=True)
    error_status = models.CharField(blank=True, null=True, max_length=20, db_column='errStatus')
    error_last_update = models.DateTimeField(blank=True, null=True, db_column='errLastUpdate')
    correction_count = models.IntegerField(default=0, db_column='correctionCount')
    created_at = models.DateTimeField(auto_now_add=True)


class SortParameter(models.Model):
    """Модель параметра сортировки результатов запроса."""
    title_uk = models.CharField('Назва параметру (укр.)', max_length=255)
    title_en = models.CharField('Назва параметру (en.)', max_length=255)
    value = models.CharField('Значення поля', max_length=255, unique=True)
    search_field = models.ForeignKey(
        'SimpleSearchField',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пошуковий параметр',
        help_text='Пошуковий параметр, по якому відбувається сортування.'
    )
    ordering = models.CharField(
        'Напрямок сортування',
        choices=(
            ('asc', 'По зростанню'),
            ('desc', 'За спаданням')
        ),
        max_length=4
    )
    weight = models.PositiveIntegerField(
        'Вага',
        default=1000,
        help_text='Чим більша вага, тим вище елемент у списку параметрів на сторінках результатів пошуку.'
    )
    is_enabled = models.BooleanField('Відображати', default=True)

    def __str__(self):
        return self.title_uk

    class Meta:
        verbose_name = 'Параметр сортування'
        verbose_name_plural = 'Параметри сортування результатів пошуку'


class IndexationProcess(models.Model):
    """Модель процесса индексации."""
    not_indexed_count = models.PositiveIntegerField("Кількість об'єктів для індексації", default=0)
    processed_count = models.PositiveIntegerField("Опрацьовано об'єктів", default=0)
    begin_date = models.DateTimeField("Дата та час початку індексації")
    finish_date = models.DateTimeField("Дата та час закінчення індексації", null=True, blank=True)
    documents_in_index = models.PositiveIntegerField("Всього документів", null=True, blank=True)
    documents_in_index_shared = models.PositiveIntegerField("Всього документів опублікованих", null=True, blank=True)

    def __str__(self):
        return self.finish_date

    class Meta:
        verbose_name = 'Процес індексації'
        verbose_name_plural = 'Процеси індексації'


class SimpleSearchPage(models.Model):
    """Модель страниці простого поиска."""
    description_uk = RichTextUploadingField('Опис сторінки (укр.)', blank=True)
    description_en = RichTextUploadingField('Опис сторінки (англ.)', blank=True)

    def __str__(self):
        return 'Сторінка простого пошуку'

    class Meta:
        verbose_name = 'Сторінка простого пошуку'
        verbose_name_plural = 'Сторінка простого пошуку'


class AdvancedSearchPage(models.Model):
    """Модель страниці простого поиска."""
    description_uk = RichTextUploadingField('Опис сторінки (укр.)', blank=True)
    description_en = RichTextUploadingField('Опис сторінки (англ.)', blank=True)

    def __str__(self):
        return 'Сторінка простого пошуку'

    class Meta:
        verbose_name = 'Сторінка розширенного пошуку'
        verbose_name_plural = 'Сторінка розширенного пошуку'
