from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import Page

admin.site.register(Page, SingleModelAdmin)
