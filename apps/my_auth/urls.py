from django.urls import path
from .views import logout_view, get_ca_data, login_view, login_ds, login_password

app_name = 'auth'
urlpatterns = [
    path('login/', login_view, name="login"),
    path('login_ds/', login_ds, name="login_ds"),
    path('login_password/', login_password, name="login_password"),
    path('logout/', logout_view, name="logout"),
    path('get_ca_data/<int:pk>', get_ca_data, name="get_ca_data"),
]
