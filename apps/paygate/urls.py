from django.urls import path
from .views import pb

app_name = 'paygate'
urlpatterns = [
    path('pb/', pb, name="pb"),
]
