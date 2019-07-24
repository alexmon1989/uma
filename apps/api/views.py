from rest_framework import generics, exceptions
from .serializers import OpenDataSerializer
from .models import OpenData
from apps.search.models import ObjType
import datetime


class OpenDataListView(generics.ListAPIView):
    serializer_class = OpenDataSerializer

    def get_queryset(self):
        queryset = OpenData.objects.all()

        # Дата від
        date_from = self.request.query_params.get('date_from', None)
        if date_from:
            try:
                date_from = datetime.datetime.strptime(date_from, '%d.%m.%Y').strftime('%Y-%m-%d')
                queryset = queryset.filter(app__lastupdate__gte=date_from)
            except:
                raise exceptions.ParseError("Невірне значення параметру date_from")

        # Дата до
        date_to = self.request.query_params.get('date_to', None)
        if date_to:
            try:
                date_to = datetime.datetime.strptime(date_to, '%d.%m.%Y').strftime('%Y-%m-%d')
                queryset = queryset.filter(app__lastupdate__lte=date_to)
            except:
                raise exceptions.ParseError("Невірне значення параметру date_to")

        # Змінені/нові
        changed = self.request.query_params.get('changed', None)
        if changed:
            try:
                changed = int(changed)
                if changed == 0:
                    queryset = queryset.filter(app__changescount=0)
                else:
                    queryset = queryset.filter(app__changescount__gt=0)
            except ValueError:
                raise exceptions.ParseError("Невірне значення параметру changed")

        # Тип об'єкта
        obj_type = self.request.query_params.get('obj_type', None)
        if obj_type:
            try:
                obj_type = ObjType.objects.get(id=obj_type)
                queryset = queryset.filter(app__obj_type=obj_type)
            except ObjType.DoesNotExist:
                raise exceptions.ParseError("Невірне значення параметру obj_type")

        # Стан об'єкта
        obj_state = self.request.query_params.get('obj_state', None)
        if obj_state:
            try:
                obj_state = int(obj_state)
                if obj_state == 1:
                    queryset = queryset.filter(app__registration_date__isnull=True)
                elif obj_state == 2:
                    queryset = queryset.filter(app__registration_date__isnull=False)
            except ValueError:
                raise exceptions.ParseError("Невірне значення параметру obj_state")

        return queryset.values(
            'app__obj_type__obj_type_ua',
            'app__app_number',
            'app__registration_number',
            'app__registration_date',
            'app__changescount',
            'app__lastupdate',
            'data',
        )
