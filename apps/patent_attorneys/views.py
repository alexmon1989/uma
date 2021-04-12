from django.views.generic.list import ListView
from django.http import Http404

from .models import PatentAttorney

from .forms import PatentAttorneyForm


class PatentAttorneyListView(ListView):
    model = PatentAttorney
    template_name = 'patent_attorneys/list/index.html'

    def get_queryset(self):
        qs = super().get_queryset()

        # Сортировка
        if self.request.GET.get('sort_by'):
            form = PatentAttorneyForm(self.request.GET)
            if form.is_valid():
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

        return qs

    def get_paginate_by(self, queryset):
        if self.request.GET.get('show'):
            form = PatentAttorneyForm(self.request.GET)
            if form.is_valid():
                return int(self.request.GET['show'])
            else:
                raise Http404
        return 10
