from django.urls import path
from .views import OpenDataListView

app_name = 'api'
urlpatterns = [
    path('v0/open-data/', OpenDataListView.as_view()),
]
