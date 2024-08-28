import base64

from django.contrib import admin
from django.utils.html import format_html

from .forms import WKMMarkAdminForm
from .models import WKMMark, WKMMarkOwner, WKMRefOwner, WKMRefBulletin, WKMClass, WKMVienna


class MultiDBModelAdmin(admin.ModelAdmin):
    # A handy constant for the name of the alternate database.
    using = "WellKnownMarks"

    def save_model(self, request, obj, form, change):
        # Tell Django to save objects to the 'other' database.
        obj.save(using=self.using)

    def delete_model(self, request, obj):
        # Tell Django to delete objects from the 'other' database
        obj.delete(using=self.using)

    def get_queryset(self, request):
        # Tell Django to look for objects on the 'other' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super().formfield_for_foreignkey(
            db_field, request, using=self.using, **kwargs
        )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super().formfield_for_manytomany(
            db_field, request, using=self.using, **kwargs
        )


class MultiDBStackedInline(admin.StackedInline):
    using = "WellKnownMarks"

    def get_queryset(self, request):
        # Tell Django to look for inline objects on the 'other' database.
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Tell Django to populate ForeignKey widgets using a query
        # on the 'other' database.
        return super().formfield_for_foreignkey(
            db_field, request, using=self.using, **kwargs
        )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Tell Django to populate ManyToMany widgets using a query
        # on the 'other' database.
        return super().formfield_for_manytomany(
            db_field, request, using=self.using, **kwargs
        )


class WKMClassInline(MultiDBStackedInline):
    model = WKMClass
    extra = 0


class WKMOwnerInline(MultiDBStackedInline):
    model = WKMMarkOwner
    extra = 0


class WKMViennaInline(MultiDBStackedInline):
    model = WKMVienna
    extra = 0


@admin.register(WKMMark)
class WKMMarkAdmin(MultiDBModelAdmin):
    list_display = ('keywords', 'bulletin')
    ordering = ('id', )
    search_fields = ('keywords', )
    inlines = (
        WKMClassInline,
        WKMViennaInline,
        WKMOwnerInline,
    )
    form = WKMMarkAdminForm

    def image_tag(self, obj):
        if obj.mark_image:
            image_data = base64.b64encode(obj.mark_image).decode('utf-8')
            return format_html(f'<img src="data:image/jpeg;base64,{image_data}" width="150" />')
        return 'Зображення відсутнє'

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


@admin.register(WKMRefBulletin)
class WKMRefBulletinAdmin(MultiDBModelAdmin):
    list_display = ('bull_str', 'bulletin_date', 'bulletin_number', )


@admin.register(WKMRefOwner)
class WKMRefOwnerAdmin(MultiDBModelAdmin):
    list_display = ('owner_name', 'country_code', )
