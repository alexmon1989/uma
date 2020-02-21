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


class DashboardView(LoginRequiredMixin, TemplateView):
    """Отображает стартовую страницу кабинета пользователя."""
    template_name = "accounts/dashboard/index.html"


class AccountBalanceView(LoginRequiredMixin, ListView):
    """Отображает страницу состояния баланса пользователя, а также операции с балансом."""
    model = BalanceOperation
    template_name = "accounts/account_balance/index.html"

    def get_queryset(self):
        return self.request.user.balance.balanceoperation_set.all().order_by('-created_at')


class DepositView(LoginRequiredMixin, FormView):
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


class MessagesListView(LoginRequiredMixin, ListView):
    """Отображает страницу списка системных сообщений."""
    template_name = "accounts/messages/list.html"
    model = Message
    queryset = Message.objects.filter(is_published=True).order_by('-created_at')


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
        lic, created = License.objects.get_or_create()
        initial['license_confirmed'] = self.request.user in lic.users.all()
        return initial

    def form_valid(self, form):
        self.request.user.email = form.cleaned_data['email']
        self.request.user.save()
        lic, created = License.objects.get_or_create()
        if form.cleaned_data['license_confirmed']:
            if self.request.user not in lic.users.all():
                lic.users.add(self.request.user)
        else:
            lic.users.remove(self.request.user)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['license'], created = License.objects.get_or_create()
        return context
