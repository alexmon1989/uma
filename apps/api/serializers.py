from django.conf import settings
from rest_framework import serializers
from .models import OpenData
import json
from datetime import datetime


class OpenDataSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True, source="app_id")
    obj_type = serializers.CharField(read_only=True, source="obj_type__obj_type_ua")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['data'] = json.loads(ret['data'])

        # Если это знак для товаров, то необходимо указывать полные пути к изображениям
        try:
            image_name = ret['data']['MarkImageDetails']['MarkImage']['MarkImageFilename']
            year = datetime.strptime(ret['data']['ApplicationDate'], '%Y-%m-%d').year
            file_path = f"{settings.MEDIA_URL}TRADE_MARKS/{year}/{ret['app_number']}/{image_name}"
            ret['data']['MarkImageDetails']['MarkImage']['MarkImageFilename'] = file_path
        except KeyError:
            pass

        # Если это пром. образец, то необходимо указывать полные пути к изображениям
        try:
            images = ret['data']['DesignSpecimenDetails'][0]['DesignSpecimen']
            for image in images:
                image_name = image['SpecimenFilename']
                year = datetime.strptime(ret['data']['DesignApplicationDate'], '%Y-%m-%d').year
                file_path = f"{settings.MEDIA_URL}INDUSTRIAL_DES/{year}/{ret['app_number']}/{image_name}"
                image['SpecimenFilename'] = file_path
        except KeyError:
            pass

        return ret

    class Meta:
        model = OpenData
        fields = (
            'id',
            'obj_type',
            'app_number',
            'registration_number',
            'registration_date',
            'last_update',
            'data',
        )


class OpenDataSerializerV1(OpenDataSerializer):
    class Meta:
        model = OpenData
        fields = (
            'id',
            'obj_type',
            'obj_state',
            'app_number',
            'app_date',
            'registration_number',
            'registration_date',
            'last_update',
            'data',
        )
