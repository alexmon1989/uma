from django.urls import path
from .views import (SimpleListView, AdvancedListView, add_filter_params, ObjectDetailView, download_docs_zipped,
                    download_doc, download_selection, download_xls_simple, download_xls_advanced, download_shared_docs,
                    TransactionsSearchView, download_xls_transactions, get_results_html, get_data_app_html,
                    get_obj_types_with_transactions, GetAccessToAppRedirectView, get_validation_info)

app_name = 'search'
urlpatterns = [
    path('simple/', SimpleListView.as_view(), name="simple"),
    path('advanced/', AdvancedListView.as_view(), name="advanced"),
    path('transactions/', TransactionsSearchView.as_view(), name="transactions"),
    path('detail/<int:pk>/', ObjectDetailView.as_view(), name="detail"),
    path('get-access-app/<int:pk>/', GetAccessToAppRedirectView.as_view(), name="get-access-app"),
    path('get-data-app/', get_data_app_html, name="get_data_app_html"),
    path('get-validation-info/', get_validation_info, name="get_validation_info"),
    path('add_filter_params/', add_filter_params, name="add_filter_params"),
    path('download-docs/', download_docs_zipped, name="download_docs_zipped"),
    path('download-doc/<int:id_app_number>/<int:id_cead_doc>/', download_doc, name="download_doc"),
    path(
        'download-selection/<int:id_app_number>/',
        download_selection,
        name="download_selection"
    ),
    path('download-xls-simple/', download_xls_simple, name="download_xls_simple"),
    path('download-xls-advanced/', download_xls_advanced, name="download_xls_advanced"),
    path('download-xls-transactions/', download_xls_transactions, name="download_xls_transactions"),
    path('download_shared_docs/<int:id_app_number>/', download_shared_docs, name="download_shared_docs"),
    path('results/', get_results_html, name="get_results_html"),
    path('get_obj_types_with_transactions/', get_obj_types_with_transactions, name="get_obj_types_with_transactions"),
]
