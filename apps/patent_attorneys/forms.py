from django import forms


class PatentAttorneyForm(forms.Form):
    sort_by = forms.ChoiceField(
        choices=(
            ('regnum_asc', 'regnum_asc'),
            ('regnum_desc', 'regnum_desc'),
            ('regdate_asc', 'regdate_asc'),
            ('regdate_desc', 'regdate_desc'),
            ('name_asc', 'name_asc'),
            ('name_desc', 'name_desc'),
        ),
        required=False
    )
    show = forms.ChoiceField(
        choices=(
            ('10', 10),
            ('20', 20),
            ('50', 50),
            ('100', 100),
        ),
        required=False
    )
