from django.urls import path
from .views import SimpleListView, AdvancedListView

app_name = 'search'
urlpatterns = [
    path('simple/', SimpleListView.as_view(), name="simple"),
    path('advanced/', AdvancedListView.as_view(), name="advanced"),
]
