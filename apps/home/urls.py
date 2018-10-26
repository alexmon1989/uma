from django.urls import path
from .views import index, private_page

app_name = 'home'
urlpatterns = [
    path('', index, name="index"),
    path('private/', private_page, name="private_page"),
]
