from django.urls import path
from .views import IndexView, get_results_html, ClearRedirectView, download_xls_favorites

app_name = 'favorites'

urlpatterns = [
    path('', IndexView.as_view(), name="index"),
    path('results/', get_results_html, name="get_results_html"),
    path('clear/', ClearRedirectView.as_view(), name="clear"),
    path('download-xls-favorites/', download_xls_favorites, name="download_xls_favorites"),
]
