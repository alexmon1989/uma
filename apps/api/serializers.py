from rest_framework import serializers
from .models import OpenData
import json


class OpenDataSerializer(serializers.ModelSerializer):
    obj_type = serializers.CharField(read_only=True, source="app__obj_type__obj_type_ua")
    app_number = serializers.CharField(read_only=True, source="app__app_number")
    registration_number = serializers.CharField(read_only=True, source="app__registration_number")
    registration_date = serializers.DateTimeField(read_only=True, source="app__registration_date")
    last_update = serializers.DateTimeField(read_only=True, source="app__lastupdate")
    changed = serializers.BooleanField(read_only=True, source="app__changescount")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['data'] = json.loads(ret['data'])

        return ret

    class Meta:
        model = OpenData
        fields = (
            'obj_type',
            'app_number',
            'registration_number',
            'registration_date',
            'changed',
            'last_update',
            'data',
        )
