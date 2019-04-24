from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import IpcCode, ElasticIndexField, SimpleSearchField, InidCodeSchedule, SortParameter


@admin.register(IpcCode)
class IPCCodeAdmin(admin.ModelAdmin):
    list_display = (
        'code_value_ua',
        'obj_type',
        'code_inid',
    )
    list_filter = (
        'obj_type',
    )
    search_fields = (
        'code_value_ua',
        'code_value_en',
        'obj_type__obj_type_ua',
        'obj_type__obj_type_en',
        'code_inid',
    )


class ObjStatusFilter(admin.SimpleListFilter):
    """Фильтр для статуса объекта (заявка, охранный документ)"""
    title = _("Статус об'єкта")
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('1', _('Заявка')),
            ('2', _('Охоронний документ')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            # 10, 11, 12, 13, 14, 15 - id реестров заявок
            return queryset.filter(schedule_type__id__in=(10, 11, 12, 13, 14, 15))
        if self.value() == '2':
            # 3, 4, 5, 6, 7, 8 - id реестров охранных документов
            return queryset.filter(schedule_type__id__in=(3, 4, 5, 6, 7, 8))


@admin.register(InidCodeSchedule)
class InidCodeScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'ipc_code_title',
        'obj_type',
        'obj_status',
        'elastic_index_field',
        'enable_search',
        'enable_view'
    )
    list_filter = (
        'ipc_code__obj_type',
        ObjStatusFilter
    )
    list_editable = (
        'enable_search',
        'enable_view',
        'elastic_index_field',
    )
    ordering = ('ipc_code',)

    def get_queryset(self, request):
        """Переопределение списка параметров (отсекаются "вторые" реестры заявок)."""
        return InidCodeSchedule.objects.filter(schedule_type__id__lte=15)

    def ipc_code_title(self, obj):
        if obj.ipc_code:
            return obj.ipc_code.code_value_ua
        return '-'
    ipc_code_title.short_description = _("ІНІД-код")
    ipc_code_title.admin_order_field = 'ipc_code__code_value_ua'

    def obj_type(self, obj):
        if obj.ipc_code:
            return obj.ipc_code.obj_type
        return '-'
    obj_type.short_description = _("Тип об'єкта")
    obj_type.admin_order_field = 'ipc_code__obj_type__obj_type_ua'

    def obj_status(self, obj):
        # 3, 4, 5, 6, 7, 8 - id реестров охранных документов
        if obj.schedule_type_id in (3, 4, 5, 6, 7, 8):
            return _('Охоронний документ')
        return _('Заявка')
    obj_status.short_description = _("Статус об'єкта")
    obj_status.admin_order_field = 'schedule_type'


@admin.register(ElasticIndexField)
class ElasticIndex(admin.ModelAdmin):
    list_display = (
        'field_name',
        'field_type',
        'parent',
    )
    list_filter = (
        'field_type',
    )
    search_fields = (
        'field_name',
        'field_type',
    )


@admin.register(SimpleSearchField)
class SimpleSearchFields(admin.ModelAdmin):
    list_display = (
        'field_label_ua',
        'field_label_en',
        'elastic_index_field',
        'weight',
        'is_visible',
    )
    list_filter = (
        'is_visible',
    )
    search_fields = (
        'field_label_ua',
        'field_label_en',
        'elastic_index_field',
        'field_name',
    )
    list_editable = (
        'is_visible',
        'elastic_index_field',
        'weight',
    )


@admin.register(SortParameter)
class SortParameterAdmin(admin.ModelAdmin):
    list_display = (
        'title_uk',
        'title_en',
        'value',
        'search_field',
        'ordering',
        'weight',
        'is_enabled',
    )
    list_editable = (
        'is_enabled',
        'weight',
    )