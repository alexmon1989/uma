import base64

from django.contrib import admin
from django.utils.html import format_html
from reversion.admin import VersionAdmin

from .forms import WKMMarkAdminForm
from .widgets import MyAdminSplitDateTime
from .models import WKMMark, WKMMarkOwner, WKMRefOwner, WKMRefBulletin, WKMClass, WKMVienna


class WKMClassInline(admin.StackedInline):
    model = WKMClass
    extra = 0


class WKMOwnerInline(admin.StackedInline):
    model = WKMMarkOwner
    extra = 0


class WKMViennaInline(admin.StackedInline):
    model = WKMVienna
    extra = 0


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
