from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import License


class LicenseAdmin(SingleModelAdmin):
    fields = ('text',)


admin.site.register(License, LicenseAdmin)
