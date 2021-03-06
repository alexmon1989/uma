# Generated by Django 2.0.7 on 2018-07-20 06:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_auth', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='certificateowner',
            options={'verbose_name': 'Власник сертифікату', 'verbose_name_plural': 'Власники сертифікатів'},
        ),
        migrations.AlterModelOptions(
            name='keycenter',
            options={'ordering': ('title',), 'verbose_name': 'АЦСК', 'verbose_name_plural': 'АЦСК'},
        ),
        migrations.AddField(
            model_name='certificateowner',
            name='pszSubjLocality',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Locality власника сертифіката'),
        ),
        migrations.AlterField(
            model_name='certificateowner',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Створено'),
        ),
        migrations.AlterField(
            model_name='certificateowner',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Оновлено'),
        ),
        migrations.AlterField(
            model_name='keycenter',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Створено'),
        ),
        migrations.AlterField(
            model_name='keycenter',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Оновлено'),
        ),
    ]
