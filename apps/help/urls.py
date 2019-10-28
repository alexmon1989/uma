from django.urls import path
from .views import help_page, SectionDetailView, QuestionDetailView, search

app_name = 'help'
urlpatterns = [
    path('', help_page, name="help"),
    path('section/<slug:slug>/', SectionDetailView.as_view(), name='section-detail'),
    path('question/<slug:slug>/', QuestionDetailView.as_view(), name='question-detail'),
    path('search/', search, name='help-search'),
]
