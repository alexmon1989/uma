# Generated by Django 2.1.3 on 2020-03-12 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paygate', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='value',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Сума'),
        ),
    ]