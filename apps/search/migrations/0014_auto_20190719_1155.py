# Generated by Django 2.1.3 on 2019-07-19 11:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0013_auto_20190426_1855'),
    ]

    operations = [
        migrations.AddField(
            model_name='indexationprocess',
            name='documents_in_index',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Всього документів'),
        ),
        migrations.AddField(
            model_name='indexationprocess',
            name='documents_in_index_shared',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Всього документів опублікованих'),
        ),
    ]
