# Generated by Django 2.1.3 on 2019-10-24 08:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('help', '0003_auto_20191024_0826'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='is_enabled',
            field=models.BooleanField(default=True, verbose_name='Відображати'),
        ),
        migrations.AddField(
            model_name='section',
            name='is_enabled',
            field=models.BooleanField(default=True, verbose_name='Відображати'),
        ),
        migrations.AlterField(
            model_name='question',
            name='section',
            field=models.ForeignKey(blank=True, help_text='Питання без розділу не відображаються', null=True, on_delete=django.db.models.deletion.SET_NULL, to='help.Section'),
        ),
        migrations.AlterField(
            model_name='question',
            name='weight',
            field=models.PositiveIntegerField(default=1000, help_text='Чим більша вага, тим вище на сторінці це питання', verbose_name='Вага'),
        ),
    ]