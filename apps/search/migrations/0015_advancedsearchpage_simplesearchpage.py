# Generated by Django 2.1.3 on 2019-10-10 13:38

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0014_auto_20190719_1155'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdvancedSearchPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description_uk', ckeditor_uploader.fields.RichTextUploadingField(verbose_name='Опис сторінки (укр.)')),
                ('description_en', ckeditor_uploader.fields.RichTextUploadingField(verbose_name='Опис сторінки (англ.)')),
            ],
            options={
                'verbose_name': 'Сторінка розширенного пошуку',
                'verbose_name_plural': 'Сторінка розширенного пошуку',
            },
        ),
        migrations.CreateModel(
            name='SimpleSearchPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description_uk', ckeditor_uploader.fields.RichTextUploadingField(verbose_name='Опис сторінки (укр.)')),
                ('description_en', ckeditor_uploader.fields.RichTextUploadingField(verbose_name='Опис сторінки (англ.)')),
            ],
            options={
                'verbose_name': 'Сторінка простого пошуку',
                'verbose_name_plural': 'Сторінка простого пошуку',
            },
        ),
    ]
