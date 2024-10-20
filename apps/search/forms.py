from django import forms
from django.conf import settings
from django.forms import formset_factory
from django.utils.translation import gettext as _
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q, Index
from .models import SimpleSearchField, InidCodeSchedule, ObjType, IpcCode
from .utils import prepare_query, get_transactions_types
from datetime import datetime


def get_param_type_choices():
    """Возвращает возможные варианты для поля param_type формы SimpleSearchForm."""
    return [(x.pk, x.field_label_ua) for x in SimpleSearchField.objects.filter(is_visible=True)]


def validate_query_elasticsearch(query, field):
    """Отправляет запрос на валидацию в ElasticSearch."""
    query = prepare_query(query, field)
    client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    i = Index(settings.ELASTIC_INDEX_NAME, using=client).validate_query(body={
        'query': Q(
            'query_string',
            query=query,
            default_field=field.field_name,
            default_operator='AND'
        ).to_dict()
    })
    return i['valid']


def get_search_form(search_type, get_params):
    """Валидация поискового запроса."""
    # Подготовка данных
    get_params_validation = get_params.copy()
    for key, value in get_params_validation.items():
        if len(value) == 1 and 'obj_type' not in key and 'obj_state' not in key and key != 'transaction_type':
            get_params_validation[key] = value[0]

    if search_type == 'simple':
        SimpleSearchFormSet = formset_factory(SimpleSearchForm, min_num=1, validate_min=True)
        form = SimpleSearchFormSet(get_params_validation)
    elif search_type == 'advanced':
        AdvancedFormSet = formset_factory(AdvancedSearchForm, min_num=1, validate_min=True)
        form = AdvancedFormSet(get_params_validation)
    elif search_type == 'transactions':
        get_params_validation['obj_type'] = get_params_validation['obj_type'][0]
        form = TransactionsSearchForm(get_params_validation)
    else:
        raise Exception('Неизвестный тип поиска')

    return form


class SimpleSearchForm(forms.Form):
    """Простая форма поиска."""
    value = forms.CharField()
    param_type = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(SimpleSearchForm, self).__init__(*args, **kwargs)
        self.fields['param_type'].choices = get_param_type_choices()

    def clean(self):
        """Валидация поискового запроса."""
        cleaned_data = super().clean()
        param = cleaned_data.get('param_type')
        query = cleaned_data.get('value')
        if param and query:
            elastic_field = SimpleSearchField.objects.get(pk=param).elastic_index_field

            if not elastic_field or not validate_query_elasticsearch(query, elastic_field):
                raise forms.ValidationError(
                    "Невірний запит"
                )


def get_obj_type_choices():
    """Возвращает возможные варианты для поля obj_type формы AdvancedSearchForm."""
    return [(x.id, x.obj_type_ua) for x in ObjType.objects.all()]


def get_ipc_code_choices():
    """Возвращает возможные варианты для поля ipc_code формы AdvancedSearchForm."""
    return [(x.id, x.code_value_ua) for x in IpcCode.objects.all()]


class AdvancedSearchForm(forms.Form):
    """Расширенная форма поиска."""
    obj_type = forms.MultipleChoiceField()
    obj_state = forms.MultipleChoiceField(choices=((1, 1), (2, 2)))
    ipc_code = forms.ChoiceField()
    value = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(AdvancedSearchForm, self).__init__(*args, **kwargs)
        self.fields['obj_type'].choices = get_obj_type_choices()
        self.fields['ipc_code'].choices = get_ipc_code_choices()

    def clean(self):
        """Валидация поискового запроса."""
        cleaned_data = super().clean()
        param = cleaned_data.get('ipc_code')
        query = cleaned_data.get('value')

        if param and query:
            inid_code_schedule = InidCodeSchedule.objects.filter(
                ipc_code=param,
                enable_search=1,
                elastic_index_field__isnull=False
            ).first()
            if inid_code_schedule:
                elastic_field = inid_code_schedule.elastic_index_field

            if not inid_code_schedule or not elastic_field or not validate_query_elasticsearch(query, elastic_field):
                raise forms.ValidationError(
                    "Невірний запит"
                )


class QueryForm(forms.Form):
    """Форма запроса в ElasticSearch. Необходима для валидации на стороне клиента."""
    param = forms.IntegerField()
    search_type = forms.ChoiceField(choices=(
        ('simple', 'simple'),
        ('advanced', 'advanced'),
    ))
    query = forms.CharField()

    def clean(self):
        cleaned_data = super().clean()
        param = cleaned_data.get("param")
        query = self.data['query']
        search_type = cleaned_data.get("search_type")

        if search_type == 'simple':
            try:
                elastic_field = SimpleSearchField.objects.get(pk=param).elastic_index_field
                query = prepare_simple_query(query, elastic_field.field_type)
            except SimpleSearchField.DoesNotExist:
                raise forms.ValidationError(
                    "Невірний параметр запиту"
                )
        else:
            inid_code = InidCodeSchedule.objects.filter(
                ipc_code=param,
                enable_search=1,
                elastic_index_field__isnull=False
            ).first()
            if inid_code:
                elastic_field = inid_code.elastic_index_field
                query = prepare_advanced_query(query, elastic_field.field_type)
            else:
                raise forms.ValidationError(
                    "Невірний параметр запиту"
                )

        # Валидация запроса в ElasticSearch
        client = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
        i = Index(settings.ELASTIC_INDEX_NAME, using=client).validate_query(body={
            'query': Q(
                'query_string',
                query=query,
                default_field=elastic_field.field_name,
                default_operator='AND'
            ).to_dict()
        })

        if not i['valid']:
            raise forms.ValidationError(
                "Невірний запит"
            )


class TransactionsSearchForm(forms.Form):
    """Форма поиска по оповещениям."""
    obj_type = forms.IntegerField()
    transaction_type = forms.MultipleChoiceField()
    date = forms.CharField()

    def __init__(self, *args, **kwargs):
        super(TransactionsSearchForm, self).__init__(*args, **kwargs)
        self.fields['obj_type'].choices = get_obj_type_choices()
        transaction_types = []
        try:
            transaction_types = get_transactions_types(int(self.data['obj_type']))
        except ValueError:
            pass
        self.fields['transaction_type'].choices = [(x, x) for x in transaction_types]

    def clean_date(self):
        data = self.cleaned_data['date']
        dates = data.split(' ~ ')
        try:
            date_from = datetime.strptime(dates[0], '%d.%m.%Y')
            date_to = datetime.strptime(dates[1], '%d.%m.%Y')
        except ValueError:
            raise forms.ValidationError(_("Невірний діапазон дат"))
        return {
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
        }
