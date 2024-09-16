import base64

from django.contrib import admin
from django.utils.html import format_html
from reversion.admin import VersionAdmin

from .forms import WKMMarkAdminForm, WKMDocumentAdminForm
from .widgets import MyAdminSplitDateTime
from .models import (WKMMark, WKMMarkOwner, WKMRefOwner, WKMRefBulletin, WKMClass, WKMVienna, WKMDocument,
                     WKMDocumentType)


class WKMClassInline(admin.StackedInline):
    model = WKMClass
    extra = 0


class WKMOwnerInline(admin.StackedInline):
    model = WKMMarkOwner
    extra = 0

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('owner')


class WKMViennaInline(admin.StackedInline):
    model = WKMVienna
    extra = 0


class WKMDocumentInline(admin.StackedInline):
    model = WKMDocument
    extra = 0
    form = WKMDocumentAdminForm
    fields = (
        'document_type',
        'my_file',
        'file_tag',
    )
    readonly_fields = ['file_tag']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('document_type')

    def file_tag(self, obj):
        if obj.file:
            file_data = base64.b64encode(obj.file).decode('utf-8')
            return format_html(f'<a download="{obj.pk}" href="data:application/pdf;base64,{file_data}">Переглянути</a>')
        return 'Файл відсутній'

    file_tag.short_description = 'Поточний файл'


@admin.register(WKMMark)
class WKMMarkAdmin(VersionAdmin, admin.ModelAdmin):
    list_display = (
        'keywords',
        'get_rights_date_formatted',
        'bulletin',
        'get_decision_date_formatted',
        'get_order_date_formatted',
        'order_number',
    )
    ordering = ('id', )
    search_fields = ('keywords', )
    inlines = (
        WKMClassInline,
        WKMViennaInline,
        WKMOwnerInline,
        WKMDocumentInline,
    )
    form = WKMMarkAdminForm

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in ('decision_date', 'order_date', 'rights_date'):
            kwargs['widget'] = MyAdminSplitDateTime()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def image_tag(self, obj):
        if obj.mark_image:
            image_data = base64.b64encode(obj.mark_image).decode('utf-8')
            return format_html(f'<img src="data:image/jpeg;base64,{image_data}" width="150" />')
        return 'Зображення відсутнє'

    def get_rights_date_formatted(self, obj):
        if obj:
            return obj.rights_date.strftime('%d.%m.%Y')

    def get_decision_date_formatted(self, obj):
        if obj:
            return obj.decision_date.strftime('%d.%m.%Y')

    def get_order_date_formatted(self, obj):
        if obj:
            return obj.order_date.strftime('%d.%m.%Y')

    get_rights_date_formatted.admin_order_field = 'date'
    get_rights_date_formatted.short_description = WKMMark._meta.get_field('rights_date').verbose_name

    get_decision_date_formatted.admin_order_field = 'date'
    get_decision_date_formatted.short_description = WKMMark._meta.get_field('decision_date').verbose_name

    get_order_date_formatted.admin_order_field = 'date'
    get_order_date_formatted.short_description = WKMMark._meta.get_field('order_date').verbose_name

    image_tag.short_description = 'Поточне зображення'
    readonly_fields = ['image_tag']
    fields = (
        'keywords',
        'decision_date',
        'rights_date',
        'order_date',
        'order_number',
        'court_comments_ua',
        'court_comments_rus',
        'court_comments_eng',
        'image',
        'image_tag',
        'ready_for_search_indexation',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('bulletin')


@admin.register(WKMRefBulletin)
class WKMRefBulletinAdmin(admin.ModelAdmin):
    list_display = ('bull_str', 'bulletin_date', 'bulletin_number', )


@admin.register(WKMRefOwner)
class WKMRefOwnerAdmin(admin.ModelAdmin):
    list_display = ('owner_name', 'country_code', )


@admin.register(WKMDocument)
class WKMDocumentAdmin(admin.ModelAdmin):
    list_display = ('wkm', 'document_type', )
    form = WKMDocumentAdminForm
    fields = (
        'document_type',
        'wkm',
        'my_file',
        'file_tag',
    )
    readonly_fields = ['file_tag']

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('document_type')
        return qs

    def file_tag(self, obj):
        if obj.file:
            file_data = base64.b64encode(obj.file).decode('utf-8')
            return format_html(f'<a download="{obj.pk}" href="data:application/pdf;base64,{file_data}">Переглянути</a>')
        return 'Файл відсутній'

    file_tag.short_description = 'Поточний файл'


@admin.register(WKMDocumentType)
class WKMDocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('value', )
