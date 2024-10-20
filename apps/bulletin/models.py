from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from ..search.models import ObjType


class EBulletinUnits(models.Model):
    id = models.AutoField(db_column='idUnit', primary_key=True)
    obj_type = models.ForeignKey(ObjType, models.DO_NOTHING, db_column='idObjType')
    unit_name = models.CharField(db_column='UnitName', max_length=300, blank=True, null=True)
    view_order = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cl_ebulletin_units'


class EBulletinData(models.Model):
    id = models.AutoField(db_column='idObject', primary_key=True)
    unit = models.ForeignKey('EBulletinUnits', models.DO_NOTHING, db_column='idUnit', blank=True, null=True)
    app_number = models.CharField(max_length=50, blank=True, null=True)
    publication_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ls_SIS_ebulletin_data'


class ClListOfficialBulletinsIp(models.Model):
    id = models.AutoField(db_column='idBull', primary_key=True)
    bul_date = models.DateField(db_column='Bull_Date', blank=True, null=True)
    date_from = models.DateField(db_column='Date_from', blank=True, null=True)
    date_to = models.DateField(db_column='Date_to', blank=True, null=True)
    bul_number = models.IntegerField(db_column='Bull_Number', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cl_list_official_bulletins_ip'


class Page(models.Model):
    """Модель страниці простого поиска."""
    description_uk = RichTextUploadingField('Опис сторінки (укр.)', blank=True)
    description_en = RichTextUploadingField('Опис сторінки (англ.)', blank=True)

    def __str__(self):
        return 'Сторінка простого пошуку'

    class Meta:
        verbose_name = 'Дані сторінки'
        verbose_name_plural = 'Дані сторінки'
