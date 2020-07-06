from django.urls import path
from .views import OpenDataListView, OpenDataListViewV1

app_name = 'api'
urlpatterns = [
    path('v0/open-data/', OpenDataListView.as_view()),
    path('v1/open-data/', OpenDataListViewV1.as_view()),
]
