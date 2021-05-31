from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import Group, FeeType, Page


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
    )

    search_fields = (
        'code',
        'title_uk',
        'title_en',
    )

    list_filter = (
        'group',
    )

    def get_queryset(self, request):
        return FeeType.objects.select_related('group').all()

admin.site.register(Page, SingleModelAdmin)
