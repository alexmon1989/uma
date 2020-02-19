from django.views.generic import TemplateView


class DashboardView(TemplateView):
    """Отображает стартовую страницу кабинета пользователя."""
    template_name = "accounts/dashboard/index.html"


class AccountBalanceView(TemplateView):
    """Отображает страницу состояния баланса пользователя."""
    template_name = "accounts/account_balance/index.html"


class ViewsHistoryView(TemplateView):
    """Отображает страницу истории просмотров заявок."""
    template_name = "accounts/views_history/index.html"


class MessagesListView(TemplateView):
    """Отображает страницу списка системных сообщений."""
    template_name = "accounts/messages/list.html"


class SettingsView(TemplateView):
    """Отображает страницу настроек кабинета."""
    template_name = "accounts/settings/index.html"
