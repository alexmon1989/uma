from django import forms


class AdvancedSearchForm(forms.Form):
    """Расширенная форма поиска."""
    obj_type = forms.IntegerField()
    obj_state = forms.MultipleChoiceField(choices=((1, 1), (2, 2)))
    ipc_code = forms.IntegerField()
    value = forms.CharField()
