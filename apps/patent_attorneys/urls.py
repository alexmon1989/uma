from django.urls import path
from .views import PatentAttorneyListView

app_name = 'patent_attorneys'
urlpatterns = [
    path('', PatentAttorneyListView.as_view(), name="list"),
]
