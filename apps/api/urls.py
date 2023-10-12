from django.urls import path
from .views import (OpenDataListView, OpenDataListViewV1, OpenDataDetailViewV1, OpenDataDocsView, SearchListView,
                    json_schema)

app_name = 'api'
urlpatterns = [
    path('v0/open-data/', OpenDataListView.as_view()),

    # JSON Schemas
    path('v1/open-data/json-schema/<str:obj_type>/', json_schema),

    path('v1/open-data/', OpenDataListViewV1.as_view()),
    path('v1/open-data/search/', SearchListView.as_view()),
    path('v1/open-data/<path:app_number>/', OpenDataDetailViewV1.as_view()),
    path('v1/open-data/documents/<path:app_number>/', OpenDataDocsView.as_view()),

]
