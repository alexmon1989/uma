# Generated by Django 2.1.3 on 2019-03-18 09:42

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('about', '0002_auto_20190318_0825'),
    ]

    operations = [
        migrations.RenameField(
            model_name='about',
            old_name='content',
            new_name='content_en',
        ),
        migrations.RenameField(
            model_name='about',
            old_name='title',
            new_name='title_uk',
        ),
        migrations.AddField(
            model_name='about',
            name='content_uk',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, verbose_name='Зміст'),
        ),
        migrations.AddField(
            model_name='about',
            name='title_en',
            field=models.CharField(default='About', max_length=255, verbose_name='Заголовок'),
        ),
    ]