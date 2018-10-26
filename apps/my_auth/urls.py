from django.urls import path
from .views import login_view, logout_view, get_ca_data

urlpatterns = [
    path('login/', login_view, name="login"),
    path('logout/', logout_view, name="logout"),
    path('get_ca_data/<int:pk>', get_ca_data, name="get_ca_data"),
]
