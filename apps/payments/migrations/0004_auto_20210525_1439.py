# Generated by Django 2.2.17 on 2021-05-25 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_auto_20210520_1516'),
    ]

    operations = [
        migrations.RenameField(
            model_name='feetype',
            old_name='title',
            new_name='title_uk'
        ),
        migrations.RenameField(
            model_name='group',
            old_name='title',
            new_name='title_uk',
        ),
        migrations.AddField(
            model_name='feetype',
            name='title_en',
            field=models.CharField(blank=True, default='', max_length=1024, null=True, verbose_name='Назва збору (eng.)'),
        ),
        migrations.AddField(
            model_name='group',
            name='title_en',
            field=models.CharField(blank=True, default='', max_length=255, null=True, verbose_name='Назва групи (eng.)'),
        ),
    ]
