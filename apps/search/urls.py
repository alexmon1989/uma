from django.urls import path
from .views import SimpleListView, AdvancedListView, add_filter_params, ObjectDetailView, download_docs, download_doc

app_name = 'search'
urlpatterns = [
    path('simple/', SimpleListView.as_view(), name="simple"),
    path('advanced/', AdvancedListView.as_view(), name="advanced"),
    path('detail/<int:id_app_number>/', ObjectDetailView.as_view(), name="detail"),
    path('add_filter_params/', add_filter_params, name="add_filter_params"),
    path('download-docs/', download_docs, name="download_docs"),
    path('download-doc/<int:id_app_number>/<int:id_cead_doc>/', download_doc, name="download_doc"),
]
