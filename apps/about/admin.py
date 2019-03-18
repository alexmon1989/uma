from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import About

admin.site.register(About, SingleModelAdmin)
