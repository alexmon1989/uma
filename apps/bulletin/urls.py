from django.urls import path
from .views import (index, ObjTypeViewSet, UnitTypeViewSet, YearViewSet, MonthViewSet, DateViewSet, ApplicationViewSet,
                    app_details_task, get_task_info)


app_name = 'bulletin'
urlpatterns = [
    path('', index, name="index"),
    path('obj-types/', ObjTypeViewSet.as_view()),
    path('unit-types/', UnitTypeViewSet.as_view()),
    path('years/', YearViewSet.as_view()),
    path('months/', MonthViewSet.as_view()),
    path('dates/', DateViewSet.as_view()),
    path('applications/', ApplicationViewSet.as_view()),
    path('app-details-task/', app_details_task),
    path('get-task-info/', get_task_info),
]
