import uuid
import datetime
from django.utils import dateformat
from rest_framework import serializers
from .models import EBulletinData, EBulletinUnits


class ObjTypeSerializer(serializers.ModelSerializer):
    """Сериалайзер для типов объектов интелектуальной собственности, которые есть в БД"""
    obj_type_id = serializers.CharField(read_only=True, source="obj_type__id")
    name = serializers.CharField(read_only=True, source="obj_type__obj_type_ua")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id'] = uuid.uuid4()
        ret['type'] = 'obj_type'
        ret['children'] = []

        if ret['name'] == 'Знаки для товарів і послуг':
            ret['name'] = 'Торговельні марки'
        return ret

    class Meta:
        model = EBulletinUnits
        fields = ['obj_type_id', 'name']


class UnitTypeSerializer(serializers.ModelSerializer):
    """Сериалайзер для типов объектов, которые есть в БД"""
    name = serializers.CharField(read_only=True, source="unit_name")
    unit_type_id = serializers.IntegerField(read_only=True, source="id")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id'] = uuid.uuid4()
        ret['type'] = 'unit_type'
        ret['children'] = []
        return ret

    class Meta:
        model = EBulletinUnits
        fields = ['unit_type_id', 'name']


class YearSerializer(serializers.ModelSerializer):
    """Сериалайзер для типов объектов, которые есть в БД"""
    name = serializers.CharField(read_only=True, source="publication_date__year")
    unit_type_id = serializers.IntegerField(read_only=True, source="unit__id")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id'] = uuid.uuid4()
        ret['type'] = 'year'
        ret['children'] = []
        return ret

    class Meta:
        model = EBulletinData
        fields = ['name', 'unit_type_id']


class MonthSerializer(serializers.ModelSerializer):
    """Сериалайзер для типов объектов, которые есть в БД"""
    month = serializers.IntegerField(read_only=True, source="publication_date__month")
    year = serializers.IntegerField(read_only=True, source="publication_date__year")
    unit_type_id = serializers.IntegerField(read_only=True, source="unit__id")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id'] = uuid.uuid4()
        ret['type'] = 'month'
        ret['children'] = []

        # Название месяца
        ret['name'] = dateformat.format(datetime.date(1900, int(ret['month']), 1), 'F')

        return ret

    class Meta:
        model = EBulletinData
        fields = ['month', 'year', 'unit_type_id']


class DateSerializer(serializers.ModelSerializer):
    """Сериалайзер для типов объектов, которые есть в БД"""
    unit_type_id = serializers.IntegerField(read_only=True, source="unit__id")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id'] = uuid.uuid4()
        ret['type'] = 'publication_date'
        ret['children'] = []
        ret['name'] = instance['publication_date'].strftime("%d.%m.%Y")
        return ret

    class Meta:
        model = EBulletinData
        fields = ['publication_date', 'unit_type_id']


class ApplicationSerializer(serializers.ModelSerializer):
    """Сериалайзер для типов объектов, которые есть в БД"""
    unit_type_id = serializers.IntegerField(read_only=True, source="unit__id")
    name = serializers.CharField(read_only=True, source="app_number")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id'] = uuid.uuid4()
        ret['type'] = 'application'
        return ret

    class Meta:
        model = EBulletinData
        fields = ['name', 'unit_type_id']
