from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OriginalDocumentDownloadLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('sec_code', models.CharField(db_index=True, max_length=50, verbose_name='Ідентифікатор документа')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP-адреса')),
                ('user_agent', models.CharField(blank=True, max_length=500, verbose_name='User-Agent')),
                ('file_path', models.CharField(blank=True, max_length=255, verbose_name='Шлях до сформованого файлу')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={
                'verbose_name': 'Лог отримання оригіналу документа',
                'verbose_name_plural': 'Логи отримання оригіналів документів',
                'db_table': 'services_original_document_download_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='originaldocumentdownloadlog',
            index=models.Index(fields=['created_at'], name='services_or_created_7d7301_idx'),
        ),
    ]

