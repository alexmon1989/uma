from django.urls import path
from .views import DashboardView, AccountBalanceView, MessagesListView, SettingsView, ViewsHistoryView

app_name = 'account'
urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name="dashboard"),
    path('account-balance/', AccountBalanceView.as_view(), name="account_balance"),
    path('messages-list/', MessagesListView.as_view(), name="messages_list"),
    path('settings/', SettingsView.as_view(), name="settings"),
    path('views-history/', ViewsHistoryView.as_view(), name="views_history"),
]
