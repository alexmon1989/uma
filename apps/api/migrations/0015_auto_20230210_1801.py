# Generated by Django 3.2.12 on 2023-02-10 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_auto_20211213_1900'),
    ]

    operations = [
        migrations.AddField(
            model_name='opendata',
            name='files_path',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]