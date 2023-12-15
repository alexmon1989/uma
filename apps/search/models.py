import datetime
import json

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.conf import settings
from ckeditor_uploader.fields import RichTextUploadingField
from uma.abstract_models import TimeStampedModel


class IpcAppList(models.Model):
    """
    Модель об'єкта інтелектуальної власності (заявки).
    Представляє таблицю `IPC_AppList` у базі даних.

    :cvar int id: Ідентифікатор об'єкта.
    :cvar str app_number: Номер заявки.
    :cvar str registration_number: Номер охоронного документа.
    :cvar str, datetime.datetime registration_date: Дата охоронного документа.
    :cvar int id_shedule_type: Індекс завдання з таблиці cl_sheduleTypes.
    :cvar str files_path: Шлях до каталогу з документами на файловому сховищі.
    :cvar int id_parent: Ідентифікатор охоронного документа з технологічної системи.
    :cvar int id_claim: Ідентифікатор заявки з технологічної системи.
    :cvar apps.search.models.ObjType, int obj_type: Тип об'єкта інтелектуальної власності.
    :cvar int changescount: Кількість проведених оновлень. 0 - новий запис.
    :cvar int lastupdate: Дата останнього оновлення даних заявки.
    :cvar int idstatus: Статус ОПВ (індекс idStatus з таблиці cl_ClaimStatus).
    :cvar str, datetime.datetime app_date: Дата подання заявки.
    :cvar str, datetime.datetime app_input_date: Дата надходження матеріалів заявки.
    :cvar bool elasticindexed: Ознака вказує на те, що об'єкт необхідно проіндексувати ElasticSearch.
    :cvar str, datetime.datetime notification_date: Дата останнього сповіщення.
    :cvar str, datetime.datetime last_indexation_date: Дата останнього додання даних в пошуковий індекс.
    :cvar bool in_electronic_bull: Вказує, що опубліковано в електронному бюлетені.
    :cvar bool is_limited: Ознака того, що публікація обмежена.
    :cvar bool open_data_updated: Ознака того, дані оновлено у публічному API.
    """
    id = models.AutoField(db_column='idAPPNumber', primary_key=True)
    app_number = models.CharField(db_column='APP_Number', max_length=100, blank=True, null=True)
    registration_number = models.CharField(db_column='RegistrationNumber', max_length=32, blank=True, null=True)
    registration_date = models.DateTimeField(db_column='RegistrationDate', blank=True, null=True)
    id_shedule_type = models.IntegerField(db_column='idSheduleType')
    files_path = models.CharField(db_column='FilesPath', max_length=500, blank=True, null=True)
    id_parent = models.IntegerField(db_column='idParent', blank=True, null=True)
    id_claim = models.IntegerField(db_column='idClaim', blank=True, null=True)
    obj_type = models.ForeignKey('ObjType', db_column='idObjType', blank=True, null=True, on_delete=models.CASCADE)
    changescount = models.IntegerField(db_column='ChangesCount', default=0)
    lastupdate = models.DateTimeField(db_column='LastUpdate', blank=True, null=True)
    idstatus = models.IntegerField(db_column='idStatus', blank=True, null=True)
    app_date = models.DateTimeField(db_column='APP_Date', blank=True, null=True)
    app_input_date = models.DateTimeField(db_column='app_input_date', blank=True, null=True)
    elasticindexed = models.IntegerField(db_column='ElasticIndexed', blank=True, null=True)
    notification_date = models.DateField(db_column='NotificationDate', blank=True, null=True)
    last_indexation_date = models.DateTimeField(db_column='last_indexation_date', blank=True, null=True)
    in_electronic_bull = models.BooleanField(db_column='in_electronic_bull', blank=True, null=True)
    publication_app_date = models.DateTimeField(db_column='publication_APP_date', blank=True, null=True)
    is_limited = models.BooleanField(db_column='is_limited', default=False)
    open_data_updated = models.BooleanField(db_column='open_data_updated', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'IPC_AppList'

    @property
    def real_files_path(self) -> str:
        """Повертає реальний шлях до файлів на сервері."""
        return self.files_path.replace(
            '\\\\bear\\share\\',
            settings.DOCUMENTS_MOUNT_FOLDER
        ).replace(
            'e:\\poznach_test_sis\\bear_tmpp_sis\\',
            settings.DOCUMENTS_MOUNT_FOLDER
        ).replace('\\', '/')


class AppLimited(TimeStampedModel):
    """Модель заявки, которая публикуется с ограниченнм набором данных."""
    app_number = models.CharField('Номер заявки', max_length=16, db_index=True)
    obj_type = models.ForeignKey(
        'ObjType',
        verbose_name="Тип об'єкта",
        db_column='idObjType',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    settings_json = models.TextField(
        'Налаштування',
        blank=True,
        null=True,
        help_text='Налаштування публікації у форматі JSON',
        default='{}'
    )
    reason = models.TextField('Причина обмеження даних / зняття обмежень', blank=True, null=True)
    cancelled = models.BooleanField('Обмеження зняті', default=False, null=False,
                                    help_text='Якщо опцію активовано, то дані об\'єкта відображатимуться '
                                              'у повному обсязі')

    class Meta:
        db_table = 'ls_limited_applications'
        verbose_name = 'Обмежена публікація'
        verbose_name_plural = 'Обмежені публікації'
        constraints = [
            models.UniqueConstraint(fields=['app_number', 'obj_type'], name='unique app_number_obj_type')
        ]

    def __str__(self):
        return self.app_number

    @property
    def settings_dict(self) -> dict:
        """Настройки отображения в виде словаря."""
        return json.loads(self.settings_json)

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(force_insert=False, force_update=False, using=None, update_fields=None)

        # Сброс ElasticIndexed и LastUpdate в табл. IPCAppList
        IpcAppList.objects.filter(
            app_number=self.app_number,
            obj_type_id=self.obj_type_id
        ).update(
            elasticindexed=0,
            lastupdate=datetime.datetime.now()
        )

    def delete(self, using=None, keep_parents=False):
        # Сброс ElasticIndexed и LastUpdate в табл. IPCAppList
        IpcAppList.objects.filter(
            app_number=self.app_number,
            obj_type_id=self.obj_type_id
        ).update(
            elasticindexed=0,
            lastupdate=datetime.datetime.now()
        )
        
        super().delete(using=None, keep_parents=False)


class ObjType(models.Model):
    """
        Модель типу об'єкта інтелектуальної власності.
        Представляє таблицю `cl_IP_ObjTypes` у базі даних.

        :cvar int id: Ідентифікатор об'єкта.
        :cvar int obj_type_ua: Назва типу ОПВ українською.
        :cvar int obj_type_en: Назва типу ОПВ англійською мовою.
        :cvar int order: Порядок відображення типу об'єкта у формі розширенного пошуку.
    """
    id = models.AutoField(db_column='idObjType', primary_key=True)
    obj_type_ua = models.CharField(db_column='ObjTypeUA', max_length=100)
    obj_type_en = models.CharField(db_column='ObjTypeEN', max_length=100)
    order = models.PositiveSmallIntegerField(db_column='order', blank=True, null=True)

    def __str__(self):
        return self.obj_type_ua

    class Meta:
        managed = False
        db_table = 'cl_IP_ObjTypes'


class IpcCode(models.Model):
    """Модель кода ИНИД"""
    id = models.AutoField(db_column='idIPCCode', primary_key=True)
    obj_types = models.ManyToManyField(ObjType, through='IpcCodeObjType')
    schedule_types = models.ManyToManyField('ScheduleType', through='InidCodeSchedule')
    code_value_ua = models.CharField(db_column='CodeValueUA', max_length=300, verbose_name='Назва (укр.)')
    code_value_en = models.CharField(db_column='CodeValueEN', max_length=300, verbose_name='Назва (англ.)', blank=True,
                                     null=True)
    code_data_type = models.CharField(db_column='CodeDataType', max_length=32, blank=True, null=True)
    code_xml_struct = models.CharField(db_column='CodeXMLStruct', max_length=50, blank=True, null=True)
    code_inid = models.CharField(db_column='CodeINID', max_length=20, blank=True, null=True,
                                 verbose_name='Значення коду ІНІД')

    def __str__(self):
        return self.code_value_ua

    def get_obj_types(self):
        return ", ".join([o.obj_type_ua for o in self.obj_types.all()])

    class Meta:
        managed = False
        db_table = 'cl_IPCCodes'
        verbose_name = 'Код ІНІД'
        verbose_name_plural = 'Коди ІНІД'
        ordering = ('code_inid',)


class IpcCodeObjType(models.Model):
    ipc_code = models.ForeignKey(IpcCode, on_delete=models.CASCADE, verbose_name='Код ІНІД')
    obj_type = models.ForeignKey(ObjType, on_delete=models.CASCADE, verbose_name='Тип об\'єкту')

    class Meta:
        db_table = 'cl_ipc_codes_obj_types'
        verbose_name_plural = 'Типи об\'єктів'


class ScheduleType(models.Model):
    """Модель реестра ОПС."""
    id = models.IntegerField(db_column='idSheduleType', primary_key=True)
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

    @property
    def real_file_path(self) -> str:
        """Возвращает путь к файлу на диске."""
        return self.file_name.replace("\\\\bear\\share\\", settings.DOCUMENTS_MOUNT_FOLDER).replace("\\", "/")


class OrderService(models.Model):
    """Модель таблицы ls_OrderService."""
    id = models.AutoField(db_column='idOrder', primary_key=True)
    user = models.ForeignKey(User, db_column='idUser', on_delete=models.DO_NOTHING, blank=True, null=True)
    ip_user = models.GenericIPAddressField(db_column='IP_User', max_length=100, blank=True, null=True)
    order_completed = models.BooleanField(db_column='OrderCompleted', default=0)
    app = models.ForeignKey('IpcAppList', models.CASCADE, db_column='idAPPNumber', blank=True, null=True)
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
    order = models.ForeignKey('OrderService', models.CASCADE, db_column='idOrder', blank=True, null=True)
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
    """Модель процесу індексації.

    :cvar int not_indexed_count: Кількість об'єктів для індексації.
    :cvar int processed_count: Опрацьовано об'єктів.
    :cvar str, datetime.datetime begin_date: Дата та час початку індексації.
    :cvar str, datetime.datetime finish_date: Дата та час закінчення індексації.
    :cvar int documents_in_index: Всього документів у пошуковому індексі.
    """
    not_indexed_count = models.PositiveIntegerField("Кількість об'єктів для індексації", default=0)
    processed_count = models.PositiveIntegerField("Опрацьовано об'єктів", default=0)
    begin_date = models.DateTimeField("Дата та час початку індексації")
    finish_date = models.DateTimeField("Дата та час закінчення індексації", null=True, blank=True)
    documents_in_index = models.PositiveIntegerField("Всього документів", null=True, blank=True)

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


class AppVisit(TimeStampedModel):
    """Модель для истории просмотра заявок пользователем."""
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, verbose_name='Користувач')
    app = models.ForeignKey(IpcAppList, on_delete=models.CASCADE, verbose_name='Заявка')

    def __str__(self):
        return f"Користувач {self.user.get_username_full()}, заявка {self.app.app_number}"

    class Meta:
        verbose_name = 'Перегляд заявки користувачем'
        verbose_name_plural = 'Перегляди заявок користувачами'
        indexes = [
            models.Index(fields=['created_at']),
        ]


class PaidServicesSettings(models.Model):
    """Модель настроек платных услуг."""
    enabled = models.BooleanField('Увімкнено', default=False)
    tm_app_access_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Вартість доступу до заявки на ТМ, грн',
        default=120
    )

    class Meta:
        verbose_name = 'Налаштування платних послуг'
        verbose_name_plural = 'Налаштування платних послуг'


class FvCicImporter(models.Model):
    """Модель таблицы fv_cic_importer базы данных prod-erp-cms-import"""
    id = models.BigAutoField(primary_key=True)
    claim_id = models.BigIntegerField()
    claim_number = models.CharField(max_length=30, blank=True, null=True)
    claim_od_number = models.CharField(max_length=30, blank=True, null=True)
    is_censored = models.TextField(blank=True, null=True)  # This field type is a guess.
    claim_state = models.BigIntegerField()
    app_set_date = models.DateTimeField(blank=True, null=True)
    app_input_date = models.DateTimeField()
    od_publication_date = models.DateTimeField(blank=True, null=True)
    json_cic = models.TextField(blank=True, null=True)
    json_files_info = models.TextField(blank=True, null=True)
    is_exported = models.TextField(blank=True, null=True)
    is_exported_datetime = models.DateTimeField(blank=True, null=True)
    type_code = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'fv_cic_importer'


class DeliveryDateCead(models.Model):
    """Модель таблицы ls_delivery_dates базы данных EArchive."""
    id = models.AutoField(db_column='idDelivery', primary_key=True)
    id_doc_cead = models.IntegerField(db_column='idDoc', blank=True, null=True)
    send_date = models.DateTimeField(blank=True, null=True)
    valid_send_date = models.BooleanField(blank=True, null=True)
    receive_date = models.DateTimeField(blank=True, null=True)  # дата получения документа заявителем
    valid_receive_date = models.BooleanField(blank=True, null=True)
    return_date = models.DateTimeField(blank=True, null=True)
    valid_return_date = models.BooleanField(blank=True, null=True)
    return_why = models.CharField(max_length=300, blank=True, null=True)
    iddoc_techn_sys = models.IntegerField(blank=True, null=True)
    date_send_to_cancelary = models.DateTimeField(blank=True, null=True)
    is_error = models.CharField(max_length=250, blank=True, null=True)
    exchange_command = models.CharField(max_length=250, blank=True, null=True)
    is_worked_techsys = models.IntegerField(blank=True, null=True)
    is_electronic = models.IntegerField(blank=True, null=True)
    is_bug = models.IntegerField(blank=True, null=True)
    retread_date = models.DateTimeField(blank=True, null=True)
    retread_why = models.CharField(max_length=250, blank=True, null=True)
    manual_insert = models.IntegerField(blank=True, null=True)
    exported_441_code = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ls_delivery_dates'


# WellKnownMarks DB

class WKMMark(models.Model):
    id = models.AutoField(db_column='IdMark', primary_key=True)
    decision_date = models.DateTimeField(db_column='DecisionDate')
    order_date = models.DateTimeField(db_column='OrderDate')
    order_number = models.CharField(db_column='OrderNumber', max_length=50)
    rights_date = models.DateTimeField(db_column='RightsDate')
    keywords = models.CharField(db_column='KeyWords', max_length=200, blank=True, null=True)
    mark_image = models.BinaryField(db_column='MarkImage', blank=True, null=True)
    state_id = models.SmallIntegerField(db_column='IdState')
    bulletin = models.ForeignKey('WKMRefBulletin', db_column='IdBulletin', on_delete=models.DO_NOTHING, blank=True, null=True)
    where_to_publish = models.CharField(db_column='wheretopublish', max_length=20)
    court_comments_ua = models.CharField(db_column='courtcomments', max_length=255, blank=True, null=True)
    court_comments_rus = models.CharField(db_column='courtcommentsRUS', max_length=255, blank=True, null=True)
    court_comments_eng = models.CharField(db_column='courtcommentsENG', max_length=255, blank=True, null=True)

    owners = models.ManyToManyField('WKMRefOwner', through='WKMMarkOwner')

    class Meta:
        managed = False
        db_table = 'Mark'

    def to_dict(self) -> dict:
        res = {
            'PublicationDetails': [
                {
                    'PublicationDate': self.bulletin.bulletin_date[:10],
                    'PublicationIdentifier': self.bulletin.bull_str,
                }
            ],
            'DecisionDate': self.decision_date[:10] if self.decision_date else None,
            'OrderDate': self.order_date[:10] if self.order_date else None,
            'RightsDate': self.rights_date[:10] if self.rights_date else None,
            'CourtComments': {
                'CourtCommentsUA': self.court_comments_ua,
                'CourtCommentsEN': self.court_comments_eng,
                'CourtCommentsRU': self.court_comments_rus,
            },
            'WordMarkSpecification': {
                'MarkSignificantVerbalElement': [
                    {
                        '#text': self.keywords,
                        '@sequenceNumber': 1
                    }
                ]
            },
            'HolderDetails': {
                'Holder': []
            }
        }
        for i, owner in enumerate(self.owners.all(), 1):
            res['HolderDetails']['Holder'].append(
                {
                    'HolderAddressBook': {
                        'FormattedNameAddress': {
                            'Name': {
                                'FreeFormatName': {
                                    'FreeFormatNameDetails': {
                                        'FreeFormatNameLine': owner.owner_name
                                    }
                                }
                            }
                        }
                    },
                    'HolderSequenceNumber': i
                }
            )
        return res


class WKMRefOwner(models.Model):
    id = models.AutoField(db_column='IdOwner', primary_key=True)
    owner_name = models.CharField(db_column='OwnerName', max_length=500)
    country_code = models.CharField(db_column='CountryCode', max_length=2)

    class Meta:
        managed = False
        db_table = 'ref_Owners'


class WKMMarkOwner(models.Model):
    mark = models.ForeignKey(WKMMark, db_column='IdMark', on_delete=models.DO_NOTHING)
    owner = models.ForeignKey(WKMRefOwner, on_delete=models.DO_NOTHING, db_column='IdOwner')
    ord_num = models.SmallIntegerField(db_column='OrdNum')

    class Meta:
        managed = False
        db_table = 'MarkOwners'


class WKMClass(models.Model):
    mark = models.ForeignKey(WKMMark, db_column='IdMark', on_delete=models.DO_NOTHING)
    class_number = models.SmallIntegerField(db_column='ClassNumber', primary_key=True, unique=False)
    ord_num = models.SmallIntegerField(db_column='OrdNum')
    products = models.CharField(db_column='Products', max_length=2000)

    class Meta:
        managed = False
        db_table = 'MarkProducts'


class WKMRefBulletin(models.Model):
    id = models.AutoField(db_column='IdBulletin', primary_key=True)
    bulletin_date = models.DateTimeField(db_column='BulletinDate')
    bulletin_number = models.CharField(db_column='BulletinNumber', max_length=50)
    bull_str = models.CharField(db_column='bullStr', max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ref_Bulletins'
