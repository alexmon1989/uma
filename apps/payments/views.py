from django.views.generic import DetailView
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
from rest_framework import viewsets, generics

from .serizalizers import GroupSerializer, FeeTypeSerializer, OrderSerializer, OrderStatusSerializer
from .models import Group, FeeType, Order, Page
from ..search.models import IpcAppList


def index(request):
    """Отображает страницу формирования заказа."""
    page_data, created = Page.objects.get_or_create()
    return render(request, 'payments/index/index.html', {'page_data': page_data})


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """Возвращает JSON со списком групп сборов."""
    pagination_class = None
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class FeeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Возвращает JSON со списком типов сборов для определённой группы."""
    pagination_class = None
    serializer_class = FeeTypeSerializer

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        return FeeType.objects.filter(group_id=group_id).order_by('code')


def validate_application(request, group_id, app_number):
    return JsonResponse(
        {
            'result': IpcAppList.objects.filter(app_number=app_number.strip(), obj_type__group__pk=group_id).exists()
        }
    )


class OrderCreateAPIView(generics.CreateAPIView):
    """Создаёт заказ."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def perform_create(self, serializer):
        serializer.save()
        messages.success(
            self.request, 'Замовлення було успішно створено.'
        )


class OrderStatusAPIView(generics.RetrieveAPIView):
    """Возвращает JSON заказа."""
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer


class OrderDetailView(DetailView):
    """Отображает страницу сформированного заказа."""
    model = Order
    template_name = 'payments/order_detail/index.html'
