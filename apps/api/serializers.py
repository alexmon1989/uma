from django.conf import settings
from rest_framework import serializers
from .models import OpenData
import json


class OpenDataSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True, source="app_id")
    obj_type = serializers.CharField(read_only=True, source="obj_type__obj_type_ua")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['data'] = json.loads(ret['data'])

        files_dir = instance['app__files_path'].replace('\\\\bear\share\\', settings.MEDIA_URL).replace('\\', '/')

        # Если это знак для товаров, то необходимо указывать полные пути к изображениям
        try:
            image_name = ret['data']['MarkImageDetails']['MarkImage']['MarkImageFilename']
            ret['data']['MarkImageDetails']['MarkImage']['MarkImageFilename'] = f"{files_dir}{image_name}"
        except KeyError:
            pass

        # Если это пром. образец, то необходимо указывать полные пути к изображениям
        try:
            images = ret['data']['DesignSpecimenDetails'][0]['DesignSpecimen']
            for image in images:
                image['SpecimenFilename'] = f"{files_dir}{image['SpecimenFilename']}"
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
