from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class IPCCodeAdmin(admin.ModelAdmin):
    list_display = (
        'value',
        'user',
        'paid',
        'created_at',
        'updated_at',
    )
    autocomplete_fields = ('user',)
