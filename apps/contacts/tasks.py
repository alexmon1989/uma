from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_contact_form(data):
    """Задача для отправки письма с контактной формы."""
    send_mail(**data)
