# Generated by Django 2.1.3 on 2020-02-06 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_auto_20200131_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opendata',
            name='last_update',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='opendata',
            name='registration_date',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
