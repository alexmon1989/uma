# Generated by Django 2.1.3 on 2020-02-19 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0019_appvisit'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='appvisit',
            index=models.Index(fields=['created_at'], name='search_appv_created_630d7b_idx'),
        ),
    ]