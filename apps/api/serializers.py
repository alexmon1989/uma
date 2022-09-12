from django.conf import settings
from rest_framework import serializers
from .models import OpenData

from ..search.services import services as search_services

import json


class OpenDataSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True, source="app_id")
    obj_type = serializers.CharField(read_only=True, source="obj_type__obj_type_ua")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret['data']:
            ret['data'] = json.loads(ret['data'])

            files_dir = instance['app__files_path'].replace('\\\\bear\share\\', settings.MEDIA_URL).replace('\\', '/')

            # Если это знак для товаров, то необходимо указывать полные пути к изображениям
            try:
                image_name = ret['data']['MarkImageDetails']['MarkImage']['MarkImageFilename']
                ret['data']['MarkImageDetails']['MarkImage']['MarkImageFilename'] = f"{files_dir}{image_name}"
            except (KeyError, TypeError):
                pass

            # Если это пром. образец, то необходимо указывать полные пути к изображениям
            if instance['obj_type__id'] == 6:
                # Фильтрация библиографических данных
                ret['data'] = search_services.application_prepare_biblio_data_id(ret['data'])
                try:
                    images = ret['data']['DesignSpecimenDetails'][0]['DesignSpecimen']
                    for image in images:
                        image['SpecimenFilename'] = f"{files_dir}{image['SpecimenFilename']}"
                except (KeyError, TypeError):
                    pass

            # Если это авт. право, то надо убрать DocBarCode
            try:
                doc_flow = ret['data']['DocFlow']['Documents']
                for doc in doc_flow:
                    del doc['DocRecord']['DocBarCode']
            except (KeyError, TypeError):
                pass

        if ret['data_docs']:
            ret['data_docs'] = json.loads(ret['data_docs'])
            if instance['obj_type__id'] in (1, 2, 3):
                ret['data_docs'] = search_services.application_filter_documents_im_um_ld(ret['data'], ret['data_docs'])
            elif instance['obj_type__id'] in (4, 3):
                ret['data_docs'] = search_services.application_filter_documents_tm_id(ret['data_docs'])

        if ret['data_payments']:
            ret['data_payments'] = json.loads(ret['data_payments'])

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
            'data_docs',
            'data_payments',
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
            'data_docs',
            'data_payments',
        )


class OpenDataDocsSerializer(serializers.ModelSerializer):
    documents = serializers.CharField(read_only=True, source="data_docs")

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['documents'] = json.loads(ret['documents'])
        return ret

    class Meta:
        model = OpenData
        fields = (
            'documents',
        )
