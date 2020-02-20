from django import forms


class DepositForm(forms.Form):
    value = forms.DecimalField(label='Сума поповнення', min_value=1, initial=0)
