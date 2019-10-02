from django.urls import path
from .views import original_document

app_name = 'services'
urlpatterns = [
    path('original-document/', original_document, name="original_document"),
]
