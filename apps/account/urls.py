from django.urls import path
from .views import (DashboardView, AccountBalanceView, MessagesListView, SettingsView, ViewsHistoryView, DepositView,
                    MarkMessageReadView, ConfirmLicenseView)

app_name = 'account'
urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name="dashboard"),
    path('account-balance/', AccountBalanceView.as_view(), name="account_balance"),
    path('account-balance-deposit/', DepositView.as_view(), name="account_balance_deposit"),
    path('messages-list/', MessagesListView.as_view(), name="messages_list"),
    path('mark-message-read/<int:pk>', MarkMessageReadView.as_view(), name="mark_message_read"),
    path('settings/', SettingsView.as_view(), name="settings"),
    path('views-history/', ViewsHistoryView.as_view(), name="views_history"),
    path('confirm-license/', ConfirmLicenseView.as_view(), name="confirm_license"),
]
