from django import forms
from django.template import loader
from django.conf import settings
from .models import ContactsPage
from .tasks import send_contact_form


class ContactForm(forms.Form):
    """Класс формы контактов."""
    username = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100)
    subject = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=100, required=False)
    message = forms.CharField(max_length=2048)

    def send_email(self):
        # send email using the self.cleaned_data dictionary
        html_message = loader.render_to_string(
            'contacts/email/contacts.html',
            {
                'username': self.cleaned_data['username'],
                'email': self.cleaned_data['email'],
                'subject': self.cleaned_data['subject'],
                'message': self.cleaned_data['message'],
            }
        )

        contacts_data = ContactsPage.objects.first()
        recipient_list = []
        if contacts_data.form_email_1:
            recipient_list.append(contacts_data.form_email_1)
        if contacts_data.form_email_2:
            recipient_list.append(contacts_data.form_email_2)
        if contacts_data.form_email_3:
            recipient_list.append(contacts_data.form_email_3)
        if recipient_list:
            send_contact_form.delay(
                {
                    'subject': 'Повідомлення користувача сервісу',
                    'message': '',
                    'from_email': settings.DEFAULT_FROM_EMAIL,
                    'recipient_list': recipient_list,
                    'fail_silently': False,
                    'html_message': html_message
                }
            )
