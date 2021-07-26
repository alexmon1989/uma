from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import Group, FeeType, Page, Order, OrderOperation, ServiceGroup


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'title_uk',
        'title_en',
        'get_obj_types',
        'obj_state',
        'weight'
    )

    search_fields = (
        'title_uk',
        'title_en',
    )

    list_filter = (
        'obj_types',
    )

    list_editable = (
        'weight',
    )

    def get_queryset(self, request):
        return Group.objects.prefetch_related('obj_types').all()

    def get_obj_types(self, obj):
        return obj.get_obj_types()

    get_obj_types.short_description = "Типи об'єктів"


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'title_uk',
        'title_en',
        'group',
        'needs_app_number',
        'enabled',
    )

    search_fields = (
        'code',
        'title_uk',
        'title_en',
    )

    list_filter = (
        'group',
        'needs_app_number',
    )

    list_editable = (
        'needs_app_number',
        'enabled',
    )

    def get_queryset(self, request):
        return FeeType.objects.select_related('group').all()


admin.site.register(Page, SingleModelAdmin)


class OrderOperationInline(admin.StackedInline):
    model = OrderOperation
    fields = (
        'code',
        'value',
        'pay_request_pb_xml',
        'created_at',
    )
    readonly_fields = ['created_at']

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'fee_type',
        'app_number',
        'value',
        'is_paid',
        'created_at',
    )

    fields = (
        'id',
        'fee_type',
        'app_number',
        'value',
        'is_paid',
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    inlines = [
        OrderOperationInline,
    ]

    def is_paid(self, obj):
        return obj.is_paid

    is_paid.short_description = "Сплачено"
    is_paid.boolean = True

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ServiceGroup)
class ServiceGroupAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'title',
    )
