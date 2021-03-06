# Generated by Django 2.1.3 on 2020-03-13 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paygate', '0003_payment_pay_request_pb_xml'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='value_paid',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True, verbose_name='Сума сплачена'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='value',
            field=models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Сума до оплати'),
        ),
    ]
