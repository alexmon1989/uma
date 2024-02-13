from django.contrib import admin

from reversion.admin import VersionAdmin
from .models import DocumentTypeNacp


@admin.register(DocumentTypeNacp)
class DocumentTypeNacpAdmin(VersionAdmin):
    search_fields = ('title',)
    list_filter = ('obj_types',)
    list_display = ('title', 'get_obj_types', 'enabled', 'created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('obj_types')

    @admin.display(description='Типи об\'єктів')
    def get_obj_types(self, obj) -> str:
        return "\n".join([item.obj_type_ua for item in obj.obj_types.all()])
