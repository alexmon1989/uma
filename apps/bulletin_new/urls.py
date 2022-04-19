from django.urls import path
from .views import IndexView, AppDetailView, TransactionsView


app_name = 'bulletin_new'
urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('detail/<int:pk>/', AppDetailView.as_view(), name="app_detail"),
    path('transactions/<int:bul_id>/<int:transaction_type_id>/', TransactionsView.as_view(), name="transactions"),
]
