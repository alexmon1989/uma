# Generated by Django 2.1.3 on 2020-04-03 11:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0023_paidservicessettings_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='IpcCodeObjType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ipc_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='search.IpcCode')),
                ('obj_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='search.ObjType')),
            ],
            options={
                'db_table': 'cl_ipc_codes_obj_types',
            },
        ),
    ]
