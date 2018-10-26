from django.contrib import admin
from .models import IpcCode, ElasticIndexField, SimpleSearchField


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
