from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import BalanceOperation
from .forms import DepositForm
from ..search.models import AppVisit


class DashboardView(LoginRequiredMixin, TemplateView):
    """Отображает стартовую страницу кабинета пользователя."""
    template_name = "accounts/dashboard/index.html"


class AccountBalanceView(LoginRequiredMixin, ListView):
    """Отображает страницу состояния баланса пользователя, а также операции с балансом."""
    model = BalanceOperation
    template_name = "accounts/account_balance/index.html"

    def get_queryset(self):
        return self.request.user.balance.balanceoperation_set.all().order_by('-created_at')


class DepositView(FormView):
    """Пополнение счёта."""
    template_name = 'accounts/account_balance_deposit/index.html'
    form_class = DepositForm
    success_url = reverse_lazy('account:account_balance')

    def form_valid(self, form):
        self.request.user.balance.value += form.cleaned_data['value']
        self.request.user.balance.save()
        BalanceOperation.objects.create(balance=self.request.user.balance, type=2, value=form.cleaned_data['value'])
        return super().form_valid(form)


class ViewsHistoryView(LoginRequiredMixin, ListView):
    """Отображает страницу истории просмотров заявок."""
    template_name = "accounts/views_history/index.html"
    model = AppVisit

    def get_queryset(self):
        return AppVisit.objects.filter(user=self.request.user).order_by('-created_at')


class MessagesListView(LoginRequiredMixin, TemplateView):
    """Отображает страницу списка системных сообщений."""
    template_name = "accounts/messages/list.html"


class SettingsView(LoginRequiredMixin, TemplateView):
    """Отображает страницу настроек кабинета."""
    template_name = "accounts/settings/index.html"
