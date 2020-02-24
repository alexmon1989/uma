from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import RedirectView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, reverse
from django.utils.translation import gettext as _
from django.contrib import messages
from .models import BalanceOperation, License, Message
from .forms import DepositForm, SettingsForm
from ..search.models import AppVisit
from datetime import datetime


class DashboardView(LoginRequiredMixin, TemplateView):
    """Отображает стартовую страницу кабинета пользователя."""
    template_name = "accounts/dashboard/index.html"


class AccountBalanceView(LoginRequiredMixin, ListView):
    """Отображает страницу состояния баланса пользователя, а также операции с балансом."""
    model = BalanceOperation
    template_name = "accounts/account_balance/index.html"
    paginate_by = 10

    def get_queryset(self):
        qs = self.request.user.balance.balanceoperation_set.all().order_by('-created_at')
        if self.request.GET.get('date_range'):
            try:
                date_from, date_to = self.request.GET['date_range'].split(' ~ ')
                qs = qs.filter(
                    created_at__gte=datetime.strptime(f"{date_from} 00:00:00", '%d.%m.%Y %H:%M:%S'),
                    created_at__lte=datetime.strptime(f"{date_to} 23:59:59", '%d.%m.%Y %H:%M:%S'),
                )
            except ValueError:
                pass
        return qs


class DepositView(LoginRequiredMixin, FormView):
    """Пополнение счёта."""
    template_name = 'accounts/account_balance_deposit/index.html'
    form_class = DepositForm
    success_url = reverse_lazy('account:account_balance')

    def form_valid(self, form):
        self.request.user.balance.value += form.cleaned_data['value']
        self.request.user.balance.save()
        BalanceOperation.objects.create(balance=self.request.user.balance, type=2, value=form.cleaned_data['value'])
        messages.success(
            self.request,
            f"Ваш рахунок було поповнено на {form.cleaned_data['value']} грн"
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.has_confirmed_license():
            context['license'], created = License.objects.get_or_create()
        return context


class ViewsHistoryView(LoginRequiredMixin, ListView):
    """Отображает страницу истории просмотров заявок."""
    template_name = "accounts/views_history/index.html"
    model = AppVisit
    paginate_by = 10

    def get_queryset(self):
        qs = AppVisit.objects.filter(user=self.request.user).order_by('-created_at').values('pk', 'app__id', 'app__app_number', 'created_at')
        if self.request.GET.get('date_range'):
            try:
                date_from, date_to = self.request.GET['date_range'].split(' ~ ')
                qs = qs.filter(
                    created_at__gte=datetime.strptime(f"{date_from} 00:00:00", '%d.%m.%Y %H:%M:%S'),
                    created_at__lte=datetime.strptime(f"{date_to} 23:59:59", '%d.%m.%Y %H:%M:%S'),
                )
            except ValueError:
                pass
        return qs


class MessagesListView(LoginRequiredMixin, ListView):
    """Отображает страницу списка системных сообщений."""
    template_name = "accounts/messages/list.html"
    model = Message
    queryset = Message.objects.filter(is_published=True).order_by('-created_at')
    paginate_by = 5


class MarkMessageReadView(LoginRequiredMixin, RedirectView):
    """Отмечает сообщение как прочитанное пользователем."""

    def get_redirect_url(self, *args, **kwargs):
        message = get_object_or_404(Message, pk=kwargs['pk'])

        if self.request.user not in message.users.all():
            message.users.add(self.request.user)
            messages.success(
                self.request,
                _('Повідомлення відмічене як прочитане')
            )

        return reverse('account:messages_list')


class SettingsView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    """Отображает страницу настроек кабинета."""
    template_name = "accounts/settings/index.html"
    form_class = SettingsForm
    success_url = reverse_lazy('account:settings')
    success_message = _('Дані успішно збережено')

    def get_initial(self):
        initial = super().get_initial()
        initial['email'] = self.request.user.get_email()
        lic = License.objects.first()
        initial['license_confirmed'] = self.request.user in lic.users.all()
        return initial

    def form_valid(self, form):
        self.request.user.email = form.cleaned_data['email']
        self.request.user.save()
        lic = License.objects.first()
        if form.cleaned_data['license_confirmed']:
            if self.request.user not in lic.users.all():
                lic.users.add(self.request.user)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['license'], created = License.objects.get_or_create()
        if self.request.user in context['license'].users.all():
            context['form'].fields['license_confirmed'].disabled = True
        return context


class ConfirmLicenseView(LoginRequiredMixin, RedirectView):
    """Согласие пользователя с условиями лицензии."""

    def get_redirect_url(self, *args, **kwargs):
        lic = License.objects.first()

        if self.request.user not in lic.users.all():
            lic.users.add(self.request.user)
            messages.success(
                self.request,
                _('Ви погодилися з умовами ліцензії')
            )

        return self.request.META.get('HTTP_REFERER')
