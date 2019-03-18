from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import Help

admin.site.register(Help, SingleModelAdmin)
