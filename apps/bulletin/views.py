from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from celery.result import AsyncResult
from rest_framework import generics
from .serializers import (ObjTypeSerializer, UnitTypeSerializer, YearSerializer, MonthSerializer, DateSerializer,
                          ApplicationSerializer)
from .models import EBulletinUnits, EBulletinData, Page
from .tasks import get_app_details


def index(request):
    """ОТображает страницу бюлетня."""
    # Текущий язык приложения
    lang_code = 'ua' if request.LANGUAGE_CODE == 'uk' else 'en'

    # Данные страницы
    page_data, created = Page.objects.get_or_create()

    return render(
        request,
        'bulletin/index/index.html',
        {
            'lang_code': lang_code,
            'page_description': getattr(page_data, f"description_{request.LANGUAGE_CODE}"),
        }
    )


def app_details_task(request):
    app_number = request.GET.get('app_number')

    task = get_app_details.delay(
        app_number
    )

    return JsonResponse({'task_id': task.id})


def get_task_info(request):
    """Возвращает JSON с результатами выполнения асинхронного задания."""
    task_id = request.GET.get('task_id', None)
    if task_id is not None:
        task = AsyncResult(task_id)
        data = {
            'state': task.state,
            'result': task.result,
        }
        return JsonResponse(data)
    else:
        return HttpResponse('No job id given.')


class ObjTypeViewSet(generics.ListAPIView):
    """Возвращает JSON с типами объектов инт. собственности"""
    queryset = EBulletinUnits.objects.select_related(
        'obj_type'
    ).order_by(
        'obj_type__obj_type_ua'
    ).values(
        'obj_type__obj_type_ua',
        'obj_type__id'
    ).filter(ebulletindata__isnull=False).distinct()

    serializer_class = ObjTypeSerializer
    pagination_class = None


class UnitTypeViewSet(generics.ListAPIView):
    """Возвращает JSON с типами объектов инт. собственности"""
    serializer_class = UnitTypeSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = EBulletinUnits.objects.order_by(
            'unit_name'
        ).values(
            'id',
            'unit_name'
        ).filter(ebulletindata__isnull=False)

        obj_type = self.request.query_params.get('obj_type', None)
        if obj_type:
            queryset = queryset.filter(obj_type=obj_type)

        return queryset.distinct()


class YearViewSet(generics.ListAPIView):
    """Возвращает JSON с годами"""
    serializer_class = YearSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = EBulletinData.objects.order_by(
            'publication_date__year'
        ).values(
            'publication_date__year',
            'unit__id'
        )

        unit_type = self.request.query_params.get('unit_type', None)
        if unit_type:
            queryset = queryset.filter(unit=unit_type)

        print(queryset.query)

        return queryset.distinct()


class MonthViewSet(generics.ListAPIView):
    """Возвращает JSON с месяцами"""
    serializer_class = MonthSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = EBulletinData.objects.order_by(
            'publication_date__month'
        ).values(
            'publication_date__month',
            'publication_date__year',
            'unit__id'
        )

        unit_type = self.request.query_params.get('unit_type', None)
        if unit_type:
            queryset = queryset.filter(unit=unit_type)

        year = self.request.query_params.get('year', None)
        if year:
            queryset = queryset.filter(publication_date__year=year)

        return queryset.distinct()


class DateViewSet(generics.ListAPIView):
    """Возвращает JSON с месяцами"""
    serializer_class = DateSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = EBulletinData.objects.order_by(
            'publication_date'
        ).values(
            'publication_date',
            'unit__id'
        )

        unit_type = self.request.query_params.get('unit_type', None)
        if unit_type:
            queryset = queryset.filter(unit=unit_type)

        year = self.request.query_params.get('year', None)
        if year:
            queryset = queryset.filter(publication_date__year=year)

        month = self.request.query_params.get('month', None)
        if month:
            queryset = queryset.filter(publication_date__month=month)

        return queryset.distinct()


class ApplicationViewSet(generics.ListAPIView):
    """Возвращает JSON с заявками"""
    serializer_class = ApplicationSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = EBulletinData.objects.order_by(
            'app_number'
        ).values(
            'app_number',
            'unit__id'
        )

        unit_type = self.request.query_params.get('unit_type', None)
        if unit_type:
            queryset = queryset.filter(unit=unit_type)

        publication_date = self.request.query_params.get('publication_date', None)
        if publication_date:
            queryset = queryset.filter(publication_date=publication_date)

        return queryset

