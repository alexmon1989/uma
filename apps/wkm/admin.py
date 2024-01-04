from django.contrib import admin
from .models import WKMMark, WKMMarkOwner, WKMRefOwner, WKMRefBulletin, WKMClass, WKMVienna


class WKMClassInline(admin.StackedInline):
    model = WKMClass
    extra = 0


class WKMOwnerInline(admin.StackedInline):
    model = WKMMarkOwner
    extra = 0

    def __init__(self, parent_model, admin_site):
        super(WKMOwnerInline, self).__init__(parent_model, admin_site)


class WKMViennaInline(admin.StackedInline):
    model = WKMVienna
    extra = 0


@admin.register(WKMMark)
class WKMMarkAdmin(admin.ModelAdmin):
    list_display = ('keywords', 'bulletin')
    exclude = ('state_id', 'where_to_publish')
    ordering = ('id', )
    search_fields = ('keywords', )
    inlines = (
        WKMClassInline,
        WKMViennaInline,
        WKMOwnerInline,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('bulletin')


@admin.register(WKMRefBulletin)
class WKMRefBulletinAdmin(admin.ModelAdmin):
    list_display = ('bull_str', 'bulletin_date', 'bulletin_number', )


@admin.register(WKMRefOwner)
class WKMRefOwnerAdmin(admin.ModelAdmin):
    list_display = ('owner_name', 'country_code', )
