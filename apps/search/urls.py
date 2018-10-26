from django.urls import path
from .views import simple, AdvancedListView

app_name = 'search'
urlpatterns = [
    path('simple/', simple, name="simple"),
    path('advanced/', AdvancedListView.as_view(), name="advanced"),
]
