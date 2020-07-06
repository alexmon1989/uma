from django.urls import path
from .views import original_document, api_description

app_name = 'services'
urlpatterns = [
    path('original-document/', original_document, name="original_document"),
    path('api-description/', api_description, name="api_description"),
]
