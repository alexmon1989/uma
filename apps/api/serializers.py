from rest_framework import serializers
from .models import OpenData

from apps.search.services import services as search_services
from apps.api.services import services as api_services

import json


class OpenDataSerializer(serializers.ModelSerializer):
    obj_type = serializers.CharField(read_only=True, source="obj_type__obj_type_ua")

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if ret['data']:
            # Подготовка библиографических данных
            biblio_data_presenter = api_services.BiblioDataFullPresenter()
            biblio_data_presenter.set_application_data(instance)
            ret['data'] = biblio_data_presenter.get_prepared_biblio()
        else:
            ret['data'] = {}

        if ret['data_docs'] and ret['data_docs'] != 'null':
            ret['data_docs'] = json.loads(ret['data_docs'])
            if instance['obj_type_id'] in (1, 2, 3):
                ret['data_docs'] = search_services.application_filter_documents_im_um_ld(ret['data'], ret['data_docs'])
            elif instance['obj_type_id'] in (4, 6):
                ret['data_docs'] = search_services.application_filter_documents_tm_id(ret['data_docs'])
                documents_data_presenter = api_services.DocumentsDataPresenterTmId()
                documents_data_presenter.set_documents_data(ret['data_docs'])
                ret['data_docs'] = documents_data_presenter.get_prepared_documents()

        else:
            ret['data_docs'] = []

        if ret['data_payments']:
            ret['data_payments'] = json.loads(ret['data_payments'])
            if ret['obj_type_id'] in (4, 6):
                payments_data_presenter = api_services.PaymentsDataPresenterTmId()
                payments_data_presenter.set_payments_data(ret['data_payments'])
                ret['data_payments'] = payments_data_presenter.get_prepared_payments()
        else:
            ret['data_payments'] = []

        return ret

    class Meta:
        model = OpenData
        fields = (
            'obj_type',
            'obj_type_id',
            'app_number',
            'registration_number',
            'registration_date',
            'last_update',
            'data',
            'data_docs',
            'data_payments',
        )


class OpenDataSerializerV1(OpenDataSerializer):
    files = serializers.ListField(child=serializers.CharField())

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if len(ret['files']) == 0:
            del ret['files']
        return ret

    class Meta:
        model = OpenData
        fields = (
            'obj_type',
            'obj_type_id',
            'obj_state',
            'app_number',
            'app_date',
            'registration_number',
            'registration_date',
            'last_update',
            'data',
            'data_docs',
            'data_payments',
            'files',
        )


class OpenDataSerializerNacpV1(serializers.ModelSerializer):
    obj_type = serializers.CharField(read_only=True, source="obj_type__obj_type_ua")

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        if ret['data']:
            # Подготовка библиографических данных
            biblio_data_presenter = api_services.BiblioDataNacpPresenter()
            biblio_data_presenter.set_application_data(instance)
            ret['data'] = biblio_data_presenter.get_prepared_biblio()

        return ret

    class Meta:
        model = OpenData
        fields = (
            'obj_type',
            'obj_type_id',
            'obj_state',
            'app_number',
            'app_date',
            'registration_number',
            'registration_date',
            'last_update',
            'data',
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
