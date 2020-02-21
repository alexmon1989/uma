from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import License, Message


@admin.register(License)
class LicenseAdmin(SingleModelAdmin):
    fields = ('text',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'created_at')
    exclude = ('users',)
