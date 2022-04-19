from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import index, GroupViewSet, FeeTypeViewSet, validate_application, OrderDetailView

app_name = 'payments'

urlpatterns = [
    path('', index, name="index"),
    path('api/validate-application/<int:group_id>/<str:app_number>/',
         validate_application,
         name="validate_application"),
    path('order/<int:pk>/', OrderDetailView.as_view(), name='order-detail')
]

# DRF
router = DefaultRouter()
router.register(r'api/groups', GroupViewSet, basename='groups')
router.register(r'api/fee-types/(?P<group_id>\d+)', FeeTypeViewSet, basename='fee_types')

urlpatterns += router.urls
