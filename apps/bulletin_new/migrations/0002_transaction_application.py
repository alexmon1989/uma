# Generated by Django 2.2.17 on 2021-02-14 12:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0025_auto_20200611_1408'),
        ('bulletin_new', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='application',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='search.IpcAppList', verbose_name='Заявка'),
        ),
    ]