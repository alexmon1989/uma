from django.db import models
from ..search.models import ObjType, ScheduleType, IpcAppList


class EBulletinUnitHeader(models.Model):
    id = models.AutoField(primary_key=True, db_column='id_header',)
    header_ua = models.CharField(max_length=500, blank=True, null=True)
    header_en = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cl_bulletin_unit_headers'


class EBulletinUnit(models.Model):
    id = models.AutoField(primary_key=True,  db_column='id_unit')
    obj_type = models.ForeignKey(ObjType, models.DO_NOTHING, db_column='id_obj_type', blank=True, null=True)
    schedule_type = models.ForeignKey(ScheduleType, models.DO_NOTHING, db_column='id_shedule_type', blank=True,
                                      null=True)
    unit_name_ua = models.CharField(max_length=500, blank=True, null=True)
    unit_name_en = models.CharField(max_length=500, blank=True, null=True)
    unit_header = models.ForeignKey(EBulletinUnitHeader, models.DO_NOTHING, db_column='id_header_name', blank=True,
                                    null=True)
    view_order = models.IntegerField(blank=True, null=True)
    sql_query = models.TextField(blank=True, null=True)
    unit_type = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cl_ebulletin_units_new'


class Bulletin(models.Model):
    id = models.AutoField(db_column='idBull', primary_key=True)
    bul_date = models.DateField(db_column='Bull_Date', blank=True, null=True)
    date_from = models.DateField(db_column='Date_from', blank=True, null=True)
    date_to = models.DateField(db_column='Date_to', blank=True, null=True)
    bul_number = models.IntegerField(db_column='Bull_Number', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cl_list_official_bulletins_ip'


class EBulletinData(models.Model):
    id = models.AutoField(db_column='id_object', primary_key=True)
    unit = models.ForeignKey(EBulletinUnit, models.DO_NOTHING, db_column='id_unit', blank=True, null=True)
    app_number = models.CharField(max_length=50, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)
    json_data = models.TextField(blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    app = models.ForeignKey(IpcAppList, models.DO_NOTHING, db_column='idAPPNumber', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ls_SIS_ebulletin_data_new'


class TransactionType(models.Model):
    """Модель типа уведомления (сповіщення)."""
    title = models.CharField('Тип сповіщення', max_length=1024)
    obj_type = models.ForeignKey(ObjType, on_delete=models.CASCADE, verbose_name='Тип ОПВ')

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'bulletin_transaction_type'


class Transaction(models.Model):
    """Модель оповещения (сповіщення)."""
    bulletin = models.ForeignKey(Bulletin, on_delete=models.CASCADE, verbose_name='Тип ОПВ')
    json_data = models.TextField('Дані сповіщення у форматі JSON.')
    transaction_type = models.ForeignKey(TransactionType, on_delete=models.CASCADE, verbose_name='Тип сповіщення')
    application = models.ForeignKey(IpcAppList, on_delete=models.SET_NULL, verbose_name='Заявка', null=True)

    class Meta:
        db_table = 'bulletin_transaction'
