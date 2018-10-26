from django import forms
from django.core.validators import FileExtensionValidator
from apps.my_auth.models import KeyCenter


class AuthForm(forms.Form):
    """Форма авторизации с помощью ЭЦП."""
    ca = forms.ModelChoiceField(label='АЦСК', queryset=KeyCenter.objects.all())
    key_file = forms.FileField(label='Файл ключа')
    password = forms.CharField(label='Пароль сертифікату', widget=forms.PasswordInput())
    cert_file = forms.FileField(label='Файл з сертифікатом', required=False,
                                validators=[FileExtensionValidator(['cer', 'crt'])])

    def clean_cert_file(self):
        """Валидация поля 'Файл з сертифікатом'"""
        data = self.cleaned_data['cert_file']
        if not self.cleaned_data['ca'].cmpAddress and not self.cleaned_data['cert_file']:
            raise forms.ValidationError("Необхідно прикріпити файл з сертифікатом")
        return data
