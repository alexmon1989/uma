# Generated by Django 2.1.3 on 2019-10-10 13:47

import ckeditor_uploader.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0015_advancedsearchpage_simplesearchpage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advancedsearchpage',
            name='description_en',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, verbose_name='Опис сторінки (англ.)'),
        ),
        migrations.AlterField(
            model_name='advancedsearchpage',
            name='description_uk',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, verbose_name='Опис сторінки (укр.)'),
        ),
    ]