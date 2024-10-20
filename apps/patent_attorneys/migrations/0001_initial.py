# Generated by Django 2.2.17 on 2021-05-20 09:25

from django.db import migrations, models
import sys


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PatentAttorney',
            fields=[
                ('id', models.AutoField(db_column='Id', primary_key=True, serialize=False)),
                ('reg_num', models.IntegerField(blank=True, db_column='Reg_Num', null=True)),
                ('dat_reg', models.DateTimeField(blank=True, db_column='Dat_Reg', null=True)),
                ('dat_at_kom', models.DateTimeField(blank=True, db_column='Dat_At_Kom', null=True)),
                ('num_at_kom', models.IntegerField(blank=True, db_column='Num_At_Kom', null=True)),
                ('dat_nakaz', models.DateTimeField(blank=True, db_column='Dat_Nakaz', null=True)),
                ('num_nakaz', models.IntegerField(blank=True, db_column='Num_Nakaz', null=True)),
                ('prizv', models.CharField(blank=True, db_column='Prizv', max_length=50, null=True)),
                ('name', models.CharField(blank=True, db_column='Name', max_length=50, null=True)),
                ('po_batk', models.CharField(blank=True, db_column='Po_Batk', max_length=50, null=True)),
                ('special', models.CharField(blank=True, db_column='Special', max_length=500, null=True)),
                ('mis_rob', models.CharField(blank=True, db_column='Mis_Rob', max_length=450, null=True)),
                ('list_index', models.CharField(blank=True, db_column='List_Index', max_length=10, null=True)),
                ('list_oblast', models.CharField(blank=True, db_column='List_Oblast', max_length=300, null=True)),
                ('list_misto', models.CharField(blank=True, db_column='List_Misto', max_length=300, null=True)),
                ('list_street', models.CharField(blank=True, db_column='List_Street', max_length=300, null=True)),
                ('prog_index', models.CharField(blank=True, db_column='Prog_Index', max_length=10, null=True)),
                ('prog_oblast', models.CharField(blank=True, db_column='Prog_Oblast', max_length=30, null=True)),
                ('prog_misto', models.CharField(blank=True, db_column='Prog_Misto', max_length=30, null=True)),
                ('prog_street', models.CharField(blank=True, db_column='Prog_Street', max_length=300, null=True)),
                ('e_mail', models.CharField(blank=True, db_column='E_Mail', max_length=300, null=True)),
                ('phones', models.CharField(blank=True, db_column='Phones', max_length=300, null=True)),
                ('fax', models.CharField(blank=True, db_column='Fax', max_length=300, null=True)),
                ('web_site', models.CharField(blank=True, db_column='Web_Site', max_length=300, null=True)),
                ('stupin', models.CharField(blank=True, db_column='Stupin', max_length=300, null=True)),
                ('other', models.CharField(blank=True, db_column='Other', max_length=300, null=True)),
            ],
            options={
                'db_table': 'patent_attorneys',
                'ordering': ('reg_num',),
                'managed': 'test' in sys.argv,
            },
        ),
    ]
