# Generated by Django 2.2.17 on 2021-05-20 09:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feetype',
            name='code',
            field=models.CharField(default=10000, max_length=255, verbose_name='Код сбору'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='feetype',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='payments.Group', verbose_name='Група сбору'),
        ),
        migrations.AlterField(
            model_name='feetype',
            name='title',
            field=models.CharField(max_length=255, verbose_name='Назва збору'),
        ),
    ]
