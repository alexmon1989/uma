from django.db import models
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
