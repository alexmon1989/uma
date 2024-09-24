from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from singlemodeladmin import SingleModelAdmin
from .models import (IpcCode, ElasticIndexField, SimpleSearchField, InidCodeSchedule, SortParameter, AdvancedSearchPage,
                     SimpleSearchPage, PaidServicesSettings, IpcCodeObjType, AppLimited)


admin.site.register(SimpleSearchPage, SingleModelAdmin)
admin.site.register(AdvancedSearchPage, SingleModelAdmin)
admin.site.register(PaidServicesSettings, SingleModelAdmin)


class IpcCodeObjTypeInline(admin.TabularInline):
    model = IpcCodeObjType
    extra = 1


@admin.register(IpcCode)
class IPCCodeAdmin(admin.ModelAdmin):
    inlines = (IpcCodeObjTypeInline,)
    list_display = (
        'id',
        'code_value_ua',
        'get_obj_types',
        'code_inid',
    )

    def get_queryset(self, request):
        """Переопределение списка параметров (отсекаются "вторые" реестры заявок)."""
        return IpcCode.objects.prefetch_related('obj_types').all()

    def get_obj_types(self, obj):
        return obj.get_obj_types()

    get_obj_types.short_description = "Типи об'ктів"

    # list_filter = (
    #     'obj_type',
    # )

    search_fields = (
        'code_value_ua',
        'code_value_en',
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
            return queryset.filter(schedule_type__id__in=(3, 4, 5, 6, 7, 8, 16, 17, 18, 19, 30, 32, 34))


@admin.register(InidCodeSchedule)
class InidCodeScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ipc_code_title',
        'get_obj_types',
        'obj_status',
        'elastic_index_field',
        'enable_search',
        'enable_view'
    )
    list_filter = (
        ObjStatusFilter,
    )
    list_editable = (
        'enable_search',
        'enable_view',
        'elastic_index_field',
    )
    ordering = ('ipc_code',)

    def get_queryset(self, request):
        """Переопределение списка параметров (отсекаются "вторые" реестры заявок)."""
        return InidCodeSchedule.objects.select_related(
            'ipc_code',
            'elastic_index_field'
        ).prefetch_related('ipc_code__obj_types').filter(
            Q(schedule_type__id__lte=19) | Q(schedule_type__id__in=(30, 32, 34, 35))
        ).exclude(ipc_code__obj_types=None)

    def ipc_code_title(self, obj):
        if obj.ipc_code:
            return obj.ipc_code.code_value_ua
        return '-'

    ipc_code_title.short_description = _("ІНІД-код")
    ipc_code_title.admin_order_field = 'ipc_code__code_value_ua'

    def obj_status(self, obj):
        # 3, 4, 5, 6, 7, 8 - id реестров охранных документов
        if obj.schedule_type_id in (3, 4, 5, 6, 7, 8, 16, 17, 18, 19, 30, 32, 34, 35):
            return _('Охоронний документ')
        return _('Заявка')

    obj_status.short_description = _("Статус об'єкта")
    obj_status.admin_order_field = 'schedule_type'

    def get_obj_types(self, obj):
        if obj.ipc_code:
            return obj.ipc_code.get_obj_types()
        return '-'

    get_obj_types.short_description = "Типи об'ктів"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Для того чтоб 'elastic_index_field' в list_editable не вызывал лишние запросы."""
        formfield = super(InidCodeScheduleAdmin, self).formfield_for_dbfield(db_field, request, **kwargs)

        # Кеширование вариантов выбора поля elastic_index_field
        if db_field.name == 'elastic_index_field':
            choices = getattr(request, '_elastic_index_field_choices_cache', None)
            if choices is None:
                request._elastic_index_field_choices_cache = choices = list(formfield.choices)
            formfield.choices = choices

        return formfield


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


@admin.register(AppLimited)
class AppLimitedAdmin(admin.ModelAdmin):
    list_display = (
        'app_number',
        'obj_type',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'obj_type',
    )
    search_fields = (
        'app_number',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('obj_type')
