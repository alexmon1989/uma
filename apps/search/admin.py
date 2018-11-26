from django.contrib import admin
from .models import IpcCode, ElasticIndexField, SimpleSearchField, InidCodeSchedule


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


@admin.register(InidCodeSchedule)
class InidCodeScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'ipc_code_title',
        'obj_type',
        'schedule_type',
        'elastic_index_field',
        'enable_search',
        'enable_view'
    )
    list_filter = (
        'ipc_code__obj_type',
        'schedule_type',
    )
    ordering = ('ipc_code',)

    def ipc_code_title(self, obj):
        if obj.ipc_code:
            return obj.ipc_code.code_value_ua
        return '-'
    ipc_code_title.short_description = "Код об'єкта"
    ipc_code_title.admin_order_field = 'ipc_code__code_value_ua'

    def obj_type(self, obj):
        if obj.ipc_code:
            return obj.ipc_code.obj_type
        return '-'
    obj_type.short_description = "Тип об'єкта"
    obj_type.admin_order_field = 'ipc_code__obj_type__obj_type_ua'


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
        'field_name',
        'is_visible',
    )
    list_filter = (
        'is_visible',
    )
    search_fields = (
        'field_label_ua',
        'field_label_en',
        'field_name',
    )
    list_editable = (
        'is_visible',
    )
