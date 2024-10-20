# Generated by Django 2.1.3 on 2019-03-18 08:25

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('about', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='about',
            options={'verbose_name': 'Зміст сторінки', 'verbose_name_plural': 'Зміст сторінки'},
        ),
        migrations.AlterField(
            model_name='about',
            name='content',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, verbose_name='Зміст'),
        ),
        migrations.AlterField(
            model_name='about',
            name='title',
            field=models.CharField(default='Про сервіс', max_length=255, verbose_name='Заголовок'),
        ),
    ]
