from .models import Group, FeeType, Order
from rest_framework import serializers


class GroupSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='group_title')

    class Meta:
        model = Group
        fields = ['id', 'title']


class FeeTypeSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='code_title')

    class Meta:
        model = FeeType
        fields = ['id', 'title']


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


class OrderStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ['is_paid']
