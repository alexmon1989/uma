from django.urls import path
from .views import IndexView, get_results_html

app_name = 'favorites'

urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('results/', get_results_html, name="get_results_html"),
]
