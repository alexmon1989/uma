from django import forms
from django.core.validators import FileExtensionValidator
from django.contrib.auth import authenticate
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


class AuthFormSimple(forms.Form):
    """Форма авторизации по логину и паролю."""
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=100)
    remember_me = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(AuthFormSimple, self).__init__(*args, **kwargs)

    def clean(self):
        """Проверка логина и пароля"""
        user = authenticate(
            self.request,
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password']
        )
        if not user:
            raise forms.ValidationError(
                "Невірні логін та/або пароль."
            )
