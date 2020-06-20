from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import APIDescription

admin.site.register(APIDescription, SingleModelAdmin)
