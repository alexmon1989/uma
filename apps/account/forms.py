from django import forms
from django.utils.translation import ugettext_lazy as _


class DepositForm(forms.Form):
    value = forms.DecimalField(label=_('Сума поповнення'), min_value=1, initial=0)


class SettingsForm(forms.Form):
    email = forms.EmailField(label=_('Ваш контактний E-Mail'))
    license_confirmed = forms.BooleanField(
        label=_('Я погоджуюсь з умовами договору про надання інформаційних послуг'),
        required=False,
        help_text=_('Перегляд матеріалів заявок з обмеженим доступом можливий лише на умовах <a href="#" data-toggle="modal" data-target="#modal1">цього договору</a>')
    )
