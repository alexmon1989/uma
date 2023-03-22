from django.http import Http404
from rest_framework import generics, exceptions
from .serializers import OpenDataSerializer, OpenDataSerializerV1, OpenDataDocsSerializer
from .models import OpenData
from apps.search.models import ObjType
from apps.api.services import services

from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

import datetime


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

        return queryset

    @method_decorator(cache_page(60 * 60 * 2))
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class OpenDataListViewV1(generics.ListAPIView):
    serializer_class = OpenDataSerializerV1

    @method_decorator(cache_page(60 * 60 * 2))
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    def get_queryset(self):
        filters = services.opendata_prepare_filters(self.request.query_params)
        queryset = services.opendata_get_list_queryset(filters)
        return queryset


class OpenDataDetailViewV1(generics.RetrieveAPIView):
    """Возвращает детали объекта по номеру заявки."""

    serializer_class = OpenDataSerializerV1
    lookup_field = 'app_number'

    def get_queryset(self):
        queryset = OpenData.objects.select_related('obj_type').order_by('-registration_number')

        if self.request.query_params.get('obj_type', None):
            try:
                obj_type = int(self.request.query_params['obj_type'])
                queryset = queryset.filter(obj_type=obj_type)
            except ValueError:
                raise Http404

        return queryset

    def get_object(self):
        qs = self.get_queryset().filter(app_number=self.kwargs['app_number'])

        if qs.count() > 0:
            return qs.first()
        raise Http404

    @method_decorator(cache_page(60 * 60 * 2))
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class OpenDataDocsView(generics.RetrieveAPIView):
    """Возвращает документы объекта по номеру заявки."""
    serializer_class = OpenDataDocsSerializer
    lookup_field = 'app_number'

    def get_queryset(self):
        queryset = OpenData.objects.all()

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

    @method_decorator(cache_page(60 * 60 * 2))
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class SearchListView(generics.ListAPIView):
    """Поиск в API по номеру заявки, номеру охранного документа, типу объекта."""
    serializer_class = OpenDataSerializerV1
    pagination_class = None

    def get_queryset(self):
        queryset = OpenData.objects.select_related('obj_type').order_by('pk').all()

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

        return queryset[:20]

    @method_decorator(cache_page(60 * 60 * 2))
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)
