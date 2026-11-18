from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import APIDescription, OriginalDocumentDownloadLog


class OriginalDocumentDownloadLogAdmin(admin.ModelAdmin):
    list_display = ('sec_code', 'user', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('sec_code', 'user__username', 'ip_address')
    readonly_fields = ('sec_code', 'user', 'ip_address', 'user_agent', 'file_path', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(APIDescription, SingleModelAdmin)
admin.site.register(OriginalDocumentDownloadLog, OriginalDocumentDownloadLogAdmin)
