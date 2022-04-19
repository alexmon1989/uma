from django.views.generic.list import ListView
from django.http import Http404
from django.db.models import Value
from django.db.models.functions import Concat

from .models import PatentAttorney
from .forms import SortPaginationForm, FilterForm


class PatentAttorneyListView(ListView):
    """Отображает страницу со списком патентных поверенных."""

    model = PatentAttorney
    template_name = 'patent_attorneys/list/index.html'
    sort_pagination_form = None
    filter_form = None

    def get(self, request, *args, **kwargs):
        self.sort_pagination_form = SortPaginationForm(self.request.GET)
        self.filter_form = FilterForm()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        return context

    def get_queryset(self):
        qs = super().get_queryset()

        # Сортировка
        if self.request.GET.get('sort_by'):
            if self.sort_pagination_form.is_valid():
                sort_param = self.request.GET['sort_by'].split('_')
                direction = '' if sort_param[1] == 'asc' else '-'
                if sort_param[0] == 'regnum':
                    qs = qs.order_by(f"{direction}reg_num")
                elif sort_param[0] == 'regdate':
                    qs = qs.order_by(f"{direction}dat_reg")
                elif sort_param[0] == 'name':
                    qs = qs.order_by(f"{direction}prizv", f"{direction}name", f"{direction}po_batk")
            else:
                raise Http404

        # Фильтры
        if self.request.GET.get('name') or self.request.GET.get('reg_num'):
            self.filter_form = FilterForm(self.request.GET)
            if self.filter_form.is_valid():
                if self.filter_form.cleaned_data['name']:
                    qs = qs.annotate(search_name=Concat('prizv', Value(' '), 'name', Value(' '), 'po_batk'))
                    qs = qs.filter(search_name__icontains=self.filter_form.cleaned_data['name'])

                if self.filter_form.cleaned_data['reg_num']:
                    qs = qs.filter(reg_num=self.filter_form.cleaned_data['reg_num'])

        return qs.values()

    def get_paginate_by(self, queryset):
        if self.request.GET.get('show'):
            if self.sort_pagination_form.is_valid():
                return int(self.request.GET['show'])
            else:
                raise Http404
        return 10
