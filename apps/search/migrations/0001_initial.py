# Generated by Django 2.1.1 on 2018-09-28 11:18

from django.db import migrations, models
import django.db.models.deletion
import sys


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InidCodeSchedule',
            fields=[
                ('id', models.AutoField(db_column='idLink', primary_key=True, serialize=False)),
                ('schedule_type', models.IntegerField(db_column='idSheduleType', blank=True, null=True,
                                                      verbose_name='Реєстр')),
                ('ipc_code', models.IntegerField(db_column='idIPCCode', blank=True, null=True,
                                                 verbose_name='Код ІНІД')),
                ('elastic_index_field', models.IntegerField(db_column='ElasticIndexField', blank=True, null=True,
                                                            verbose_name='Поле індексу ElasticSearch')),
                ('enable_search', models.IntegerField(blank=True, db_column='EnableSearch', null=True)),
                ('enable_view', models.IntegerField(blank=True, db_column='EnableView', null=True)),
            ],
            options={
                'db_table': 'cl_LinkShedule_INID_Codes',
                'managed': 'test' in sys.argv,
            },
        ),
        migrations.CreateModel(
            name='IpcCode',
            fields=[
                ('id', models.AutoField(db_column='idIPCCode', primary_key=True, serialize=False)),
                ('code_value_ua', models.CharField(db_column='CodeValueUA', max_length=300)),
                ('code_value_en', models.CharField(blank=True, db_column='CodeValueEN', max_length=300, null=True)),
                ('code_data_type', models.CharField(blank=True, db_column='CodeDataType', max_length=32, null=True)),
                ('code_xml_struct', models.CharField(blank=True, db_column='CodeXMLStruct', max_length=50, null=True)),
                ('code_inid', models.CharField(blank=True, db_column='CodeINID', max_length=20, null=True)),
            ],
            options={
                'db_table': 'cl_IPCCodes',
                'managed': 'test' in sys.argv,
            },
        ),
        migrations.CreateModel(
            name='ObjType',
            fields=[
                ('id', models.AutoField(db_column='idObjType', primary_key=True, serialize=False)),
                ('obj_type_ua', models.CharField(db_column='ObjTypeUA', max_length=100)),
                ('obj_type_en', models.CharField(db_column='ObjTypeEN', max_length=100)),
                ('obj_server_folder', models.CharField(blank=True, db_column='ObjServerFolder', max_length=255, null=True)),
                ('file_server_name', models.CharField(blank=True, db_column='FileServerName', max_length=250, null=True)),
                ('net_share_name', models.CharField(blank=True, db_column='NetShareName', max_length=500, null=True)),
                ('order', models.PositiveSmallIntegerField(db_column='order', blank=True, null=True)),
            ],
            options={
                'db_table': 'cl_IP_ObjTypes',
                'managed': 'test' in sys.argv,
            },
        ),
        migrations.CreateModel(
            name='ScheduleType',
            fields=[
                ('id', models.AutoField(db_column='idSheduleType', primary_key=True, serialize=False)),
                ('schedule_type', models.CharField(db_column='SheduleType', max_length=300)),
                ('run_app_name', models.CharField(blank=True, db_column='RunAppName', max_length=100, null=True)),
                ('run_app_path', models.CharField(blank=True, db_column='RunAppPath', max_length=200, null=True)),
                ('is_scheduled', models.IntegerField(blank=True, db_column='isSheduled', null=True)),
                ('mask_task_name', models.CharField(blank=True, db_column='MaskTaskName', max_length=100, null=True)),
                ('idobjtype', models.IntegerField(blank=True, db_column='idObjType', null=True)),
            ],
            options={
                'db_table': 'cl_SheduleTypes',
                'managed': 'test' in sys.argv,
            },
        ),
        migrations.CreateModel(
            name='ElasticIndex',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(max_length=255, verbose_name='Название поля в индексе ElasticSearch')),
                ('field_type', models.CharField(choices=[('integer', 'Integer'), ('keyword', 'Keyword'), ('text', 'Text'), ('date', 'Date'), ('nested', 'Nested')], max_length=255, verbose_name='Тип поля ElasticSearch')),
                ('ipc_codes', models.ManyToManyField(to='search.IpcCode', verbose_name='ІНІД-коди')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='search.ElasticIndex', verbose_name='Родительское поле (nested)')),
            ],
        ),
        migrations.CreateModel(
            name='SimpleSearchFields',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(max_length=255, verbose_name='Name поля')),
                ('field_label', models.CharField(max_length=255, verbose_name='Label поля')),
                ('is_visible', models.BooleanField(default=True, verbose_name='Відображати')),
                ('elastic_index_fields', models.ManyToManyField(to='search.ElasticIndex', verbose_name='ІНІД-коди')),
            ],
        ),
    ]
