from django.http import Http404, JsonResponse
from django.conf import settings
from django.views.decorators.cache import cache_page
from rest_framework import generics, exceptions
from .serializers import OpenDataSerializer, OpenDataSerializerV1, OpenDataSerializerNacpV1, OpenDataDocsSerializer
from .models import OpenData
from apps.search.models import ObjType
from apps.api.services import services
import datetime
import os
import json


class OpenDataListView(generics.ListAPIView):
    serializer_class = OpenDataSerializer

    def get_queryset(self):
        queryset = OpenData.objects.filter(obj_state=2).order_by('pk').all()

        # Змінені/нові
        changed = self.request.query_params.get('changed', None)
        try:
            changed = int(changed)
        except:
            raise exceptions.ParseError("Невірне значення параметру changed")

        # Дата від
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            try:
                date_from = datetime.datetime.strptime(date_from, '%d.%m.%Y').strftime('%Y-%m-%d')
                if changed:
                    queryset = queryset.filter(last_update__gte=date_from)
                else:
                    queryset = queryset.filter(registration_date__gte=date_from)
            except:
                raise exceptions.ParseError("Невірне значення параметру date_from")

        # Дата до
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            try:
                date_to = datetime.datetime.strptime(date_to, '%d.%m.%Y').strftime('%Y-%m-%d')
                if changed:
                    queryset = queryset.filter(last_update__lte=date_to)
                else:
                    queryset = queryset.filter(registration_date__lte=date_to)
            except:
                raise exceptions.ParseError("Невірне значення параметру date_to")

        # Тип об'єкта
        obj_type = self.request.query_params.get('obj_type', None)
        if obj_type:
            try:
                obj_type = ObjType.objects.get(id=obj_type)
                queryset = queryset.filter(obj_type=obj_type)
            except ObjType.DoesNotExist:
                raise exceptions.ParseError("Невірне значення параметру obj_type")

        return queryset.values()

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class OpenDataListViewV1(generics.ListAPIView):

    def get_serializer_class(self):
        data_format = self.request.GET.get('biblio_format')
        if data_format and data_format == 'nacp':
            return OpenDataSerializerNacpV1
        return OpenDataSerializerV1

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(services.opendata_get_applications(page), many=True)
            return self.get_paginated_response(serializer.data)

    def get_queryset(self):
        filters = services.opendata_prepare_filters(self.request.query_params)
        queryset = services.opendata_get_ids_queryset(filters)
        return queryset


class OpenDataDetailViewV1(generics.RetrieveAPIView):
    """Возвращает детали объекта по номеру заявки."""

    serializer_class = OpenDataSerializerV1
    lookup_field = 'app_number'

    def get_object(self):
        obj_type_id = self.request.query_params.get('obj_type', None)
        if obj_type_id:
            try:
                obj_type_id = int(obj_type_id)
            except TypeError:
                raise Http404

        res = services.opendata_get_application(self.kwargs['app_number'], obj_type_id)
        if res:
            return res
        raise Http404

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class OpenDataDocsView(generics.RetrieveAPIView):
    """Возвращает документы объекта по номеру заявки."""
    serializer_class = OpenDataDocsSerializer
    lookup_field = 'app_number'

    def get_queryset(self):
        queryset = OpenData.objects.filter(is_visible=True).all()

        if self.request.query_params.get('obj_type', None):
            try:
                obj_type = int(self.request.query_params['obj_type'])
                queryset = queryset.filter(obj_type=obj_type)
            except ValueError:
                raise Http404

        return queryset.values(
            'data_docs',
        )

    def get_object(self):
        qs = self.get_queryset().filter(app_number=self.kwargs['app_number'])

        if qs.count() > 0:
            return qs.first()
        raise Http404

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class SearchListView(generics.ListAPIView):
    """Поиск в API по номеру заявки, номеру охранного документа, типу объекта."""
    serializer_class = OpenDataSerializerV1
    pagination_class = None

    def get_queryset(self):
        queryset = OpenData.objects.filter(is_visible=True).select_related('obj_type').order_by('pk').all()

        # Тип об'єкта
        obj_type = self.request.query_params.get('obj_type', None)
        if obj_type:
            try:
                obj_type = int(obj_type)
            except:
                raise exceptions.ParseError("Невірне значення параметру obj_type")
            else:
                queryset = queryset.filter(obj_type_id=obj_type)

        strict_search = self.request.query_params.get('strict_search', False)
        app_number = self.request.query_params.get('app_number', None)
        registration_number = self.request.query_params.get('registration_number', None)
        if strict_search:
            if app_number:
                queryset = queryset.filter(app_number=app_number)
            if registration_number:
                queryset = queryset.filter(registration_number=registration_number)
        else:
            if app_number:
                queryset = queryset.filter(app_number__contains_ft=f'"*{app_number}*"')
            if registration_number:
                queryset = queryset.filter(registration_number__contains_ft=f'"*{registration_number}*"')

        queryset = queryset.values(
            'id',
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
            'obj_type__obj_type_ua',
            'files_path',
        )

        return queryset[:20]

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


@cache_page(60 * 15)
def json_schema(request, obj_type: str):
    """Отображает JSON Schema."""
    try:
        with open(os.path.join(settings.BASE_DIR, 'apps', 'api', 'json_schema', f'{obj_type}.json')) as f:
            schema = json.load(f)
    except FileNotFoundError:
        raise Http404
    return JsonResponse(schema)
