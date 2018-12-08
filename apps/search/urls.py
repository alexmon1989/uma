from django.urls import path
from .views import SimpleListView, AdvancedListView, add_filter_params

app_name = 'search'
urlpatterns = [
    path('simple/', SimpleListView.as_view(), name="simple"),
    path('advanced/', AdvancedListView.as_view(), name="advanced"),
    path('add_filter_params/', add_filter_params, name="add_filter_params"),
]
