from django.views.generic.list import ListView
from django.http import Http404

from .models import PatentAttorneyExt
from .forms import SortPaginationForm, FilterForm
from .selectors import patent_attorney_list


class PatentAttorneyListView(ListView):
    """Отображает страницу со списком патентных поверенных."""

    model = PatentAttorneyExt
    template_name = 'patent_attorneys/list/index.html'
    sort_pagination_form = None
    filter_form = None

    def get(self, request, *args, **kwargs):
        self.sort_pagination_form = SortPaginationForm(self.request.GET)
        if not self.sort_pagination_form.is_valid():
            raise Http404
        self.filter_form = FilterForm(self.request.GET)
        self.filter_form.is_valid()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        return context

    def get_queryset(self):
        return patent_attorney_list(
            name=self.filter_form.cleaned_data['name'],
            reg_num=self.filter_form.cleaned_data['reg_num'],
            special=self.filter_form.cleaned_data['special'],
            postal_address=self.filter_form.cleaned_data['postal_address'],
            sort_by=self.sort_pagination_form.cleaned_data['sort_by']
        )

    def get_paginate_by(self, queryset):
        if self.request.GET.get('show'):
            return int(self.sort_pagination_form.cleaned_data['show'])
        return 10
