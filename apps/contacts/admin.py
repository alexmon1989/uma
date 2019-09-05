from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import ContactsPage

admin.site.register(ContactsPage, SingleModelAdmin)
