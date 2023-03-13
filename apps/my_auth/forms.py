from django import forms
from django.contrib.auth import authenticate


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
        if self.cleaned_data.get('username') and self.cleaned_data.get('password'):
            user = authenticate(
                self.request,
                username=self.cleaned_data['username'],
                password=self.cleaned_data['password']
            )
            if not user:
                raise forms.ValidationError(
                    "Невірні логін та/або пароль."
                )
