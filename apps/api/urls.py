from django.urls import path
from .views import OpenDataListView, OpenDataListViewV1, OpenDataDetailViewV1, OpenDataDocsView

app_name = 'api'
urlpatterns = [
    path('v0/open-data/', OpenDataListView.as_view()),

    path('v1/open-data/', OpenDataListViewV1.as_view()),
    path('v1/open-data/<str:app_number>/', OpenDataDetailViewV1.as_view()),
    path('v1/open-data/documents/<str:app_number>/', OpenDataDocsView.as_view()),
]
