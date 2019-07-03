from django.urls import path
from .views import (SimpleListView, AdvancedListView, add_filter_params, ObjectDetailView, download_docs_zipped,
                    download_doc, download_selection_inv_um_ld, download_selection_tm, download_xls_simple,
                    download_xls_advanced, download_shared_docs, TransactionsSearchView, download_xls_transactions,
                    get_simple_results_html)

app_name = 'search'
urlpatterns = [
    path('simple/', SimpleListView.as_view(), name="simple"),
    path('advanced/', AdvancedListView.as_view(), name="advanced"),
    path('transactions/', TransactionsSearchView.as_view(), name="transactions"),
    path('detail/<int:id_app_number>/', ObjectDetailView.as_view(), name="detail"),
    path('add_filter_params/', add_filter_params, name="add_filter_params"),
    path('download-docs/', download_docs_zipped, name="download_docs_zipped"),
    path('download-doc/<int:id_app_number>/<int:id_cead_doc>/', download_doc, name="download_doc"),
    path(
        'download-selection-inv-um-ld/<int:id_app_number>/',
        download_selection_inv_um_ld,
        name="download_selection_inv_um_ld"
    ),
    path(
        'download-selection-tm/<int:id_app_number>/',
        download_selection_tm,
        name="download_selection_tm"
    ),
    path('download-xls-simple/', download_xls_simple, name="download_xls_simple"),
    path('download-xls-advanced/', download_xls_advanced, name="download_xls_advanced"),
    path('download-xls-transactions/', download_xls_transactions, name="download_xls_transactions"),
    path('download_shared_docs/<int:id_app_number>/', download_shared_docs, name="download_shared_docs"),
    path('simple/results/', get_simple_results_html, name="get_simple_results_html"),
]
