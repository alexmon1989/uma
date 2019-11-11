from django.contrib import admin
from singlemodeladmin import SingleModelAdmin
from .models import Help, Section, Question

admin.site.register(Help, SingleModelAdmin)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    """Класс для описания интерфейса администрирования модели Section."""
    ordering = ('-weight',)
    list_display = ('title_uk', 'title_en', 'weight', 'is_enabled', 'updated_at')
    list_editable = ('weight', 'is_enabled',)
    list_filter = ('is_enabled',)
    search_fields = ('title_uk', 'title_en')
    prepopulated_fields = {"slug": ("title_uk",)}


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Класс для описания интерфейса администрирования модели Question."""
    ordering = ('-weight',)
    list_display = ('title_uk', 'title_en', 'section', 'weight', 'is_enabled', 'updated_at')
    list_editable = ('weight', 'is_enabled',)
    list_filter = ('section', 'is_enabled',)
    search_fields = ('title_uk', 'title_en')
    prepopulated_fields = {"slug": ("title_uk",)}

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.prefetch_related('section')
        return queryset
