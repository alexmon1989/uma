from rest_framework import generics, exceptions
from .serializers import OpenDataSerializer, OpenDataSerializerV1
from .models import OpenData
from apps.search.models import ObjType, IpcAppList
import datetime
from django.utils.timezone import make_aware


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

        return queryset.values(
            'app_id',
            'obj_type__obj_type_ua',
            'app_number',
            'registration_number',
            'registration_date',
            'last_update',
            'data',
            'app__files_path',
        )


class OpenDataListViewV1(generics.ListAPIView):
    serializer_class = OpenDataSerializerV1

    def get_queryset(self):
        queryset = OpenData.objects.select_related('app', 'obj_type').order_by('pk').all()

        # Стан об'єкта
        obj_state = self.request.query_params.get('obj_state', None)
        if obj_state:
            try:
                obj_state = int(obj_state)
            except:
                raise exceptions.ParseError("Невірне значення параметру obj_state")
            else:
                queryset = queryset.filter(obj_state=obj_state)

        # Тип об'єкта
        obj_type = self.request.query_params.get('obj_type', None)
        if obj_type:
            try:
                obj_type = int(obj_type)
            except:
                raise exceptions.ParseError("Невірне значення параметру obj_type")
            else:
                queryset = queryset.filter(obj_type_id=obj_type)

        # Дата заявки від
        app_date_from = self.request.query_params.get('app_date_from', None)
        if app_date_from:
            try:
                app_date_from = make_aware(datetime.datetime.strptime(app_date_from, '%d.%m.%Y'))
                queryset = queryset.filter(app_date__gte=app_date_from.replace(hour=0, minute=0, second=0))
            except:
                raise exceptions.ParseError("Невірне значення параметру app_date_from")

        # Дата заявки до
        app_date_to = self.request.query_params.get('app_date_to', None)
        if app_date_to:
            try:
                app_date_to = make_aware(datetime.datetime.strptime(app_date_to, '%d.%m.%Y'))
                queryset = queryset.filter(app_date__lte=app_date_to.replace(hour=23, minute=59, second=59))
            except:
                raise exceptions.ParseError("Невірне значення параметру app_date_to")

        # Дата реєстрації від
        reg_date_from = self.request.query_params.get('reg_date_from', None)
        if reg_date_from:
            try:
                reg_date_from = make_aware(datetime.datetime.strptime(reg_date_from, '%d.%m.%Y'))
                queryset = queryset.filter(registration_date__gte=reg_date_from.replace(hour=0, minute=0, second=0))
            except:
                raise exceptions.ParseError("Невірне значення параметру reg_date_from")

        # Дата реєстрації до
        reg_date_to = self.request.query_params.get('reg_date_to', None)
        if reg_date_to:
            try:
                reg_date_to = make_aware(datetime.datetime.strptime(reg_date_to, '%d.%m.%Y'))
                queryset = queryset.filter(registration_date__lte=reg_date_to.replace(hour=23, minute=59, second=59))
            except:
                raise exceptions.ParseError("Невірне значення параметру reg_date_to")

        # Дата останньої зміни від
        last_update_from = self.request.query_params.get('last_update_from', None)
        if last_update_from:
            try:
                last_update_from = make_aware(datetime.datetime.strptime(last_update_from, '%d.%m.%Y'))
                queryset = queryset.filter(last_update__gte=last_update_from.replace(hour=0, minute=0, second=0))
            except:
                raise exceptions.ParseError("Невірне значення параметру last_update_from")

        # Дата останньої зміни до
        last_update_to = self.request.query_params.get('last_update_to', None)
        if last_update_to:
            try:
                last_update_to = make_aware(datetime.datetime.strptime(last_update_to, '%d.%m.%Y'))
                queryset = queryset.filter(last_update__lte=last_update_to.replace(hour=23, minute=59, second=59))
            except:
                raise exceptions.ParseError("Невірне значення параметру last_update_to")

        return queryset.values(
            'app_id',
            'obj_type__obj_type_ua',
            'obj_state',
            'app_number',
            'app_date',
            'registration_number',
            'registration_date',
            'last_update',
            'data',
            'app__files_path',
        )
