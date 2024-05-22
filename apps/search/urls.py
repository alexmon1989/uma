from django.urls import path
from .views import (SimpleListView, AdvancedListView, add_filter_params, ObjectDetailView, download_docs_zipped,
                    download_doc, download_selection, download_simple, download_advanced, download_shared_docs,
                    TransactionsSearchView, download_transactions, get_results_html, get_data_app_html,
                    get_obj_types_with_transactions, download_details_docx, recaptcha)

app_name = 'search'
urlpatterns = [
    path('recaptcha/', recaptcha, name="recaptcha"),
    path('simple/', SimpleListView.as_view(), name="simple"),
    path('advanced/', AdvancedListView.as_view(), name="advanced"),
    path('transactions/', TransactionsSearchView.as_view(), name="transactions"),
    path('detail/<int:pk>/', ObjectDetailView.as_view(), name="detail"),
    path('get-data-app/', get_data_app_html, name="get_data_app_html"),
    path('add_filter_params/', add_filter_params, name="add_filter_params"),
    path('download-docs/', download_docs_zipped, name="download_docs_zipped"),
    path('download-doc/<int:id_app_number>/<int:id_cead_doc>/', download_doc, name="download_doc"),
    path(
        'download-selection/<int:id_app_number>/',
        download_selection,
        name="download_selection"
    ),
    path('download-simple/<str:format_>/', download_simple, name="download_simple"),
    path('download-advanced/<str:format_>/', download_advanced, name="download_advanced"),
    path('download-transactions/<str:format_>/', download_transactions, name="download_transactions"),
    path('download-details-docx/<int:id_app_number>/', download_details_docx, name="download_details_docx"),
    path('download_shared_docs/<int:id_app_number>/', download_shared_docs, name="download_shared_docs"),
    path('results/', get_results_html, name="get_results_html"),
    path('get_obj_types_with_transactions/', get_obj_types_with_transactions, name="get_obj_types_with_transactions"),
]
