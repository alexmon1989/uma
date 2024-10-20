# Generated by Django 2.1.3 on 2019-03-18 07:48

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='About',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('content', ckeditor.fields.RichTextField(blank=True, verbose_name='Текст')),
            ],
            options={
                'verbose_name': 'Про сервіс',
                'verbose_name_plural': 'Про сервіс',
            },
        ),
    ]
