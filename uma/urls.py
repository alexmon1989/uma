"""uma URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog
from apps.search.views import validate_query, get_task_info, get_validation_info, toggle_search_form
from apps.favorites.views import add_or_remove
# from apps.bulletin_new.views import get_applications
from apps.payments.views import OrderCreateAPIView, OrderStatusAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
]

urlpatterns += i18n_patterns(
    path('', include('apps.home.urls')),
    path('auth/', include('apps.my_auth.urls')),
    path('search/', include('apps.search.urls')),
    path('contacts/', include('apps.contacts.urls')),
    path('about/', include('apps.about.urls')),
    path('help/', include('apps.help.urls')),
    path('services/patent_attorneys/', include('apps.patent_attorneys.urls')),
    path('services/', include('apps.services.urls')),
    path('favorites/', include('apps.favorites.urls')),
    path('bulletin/', include('apps.bulletin.urls')),
    # path('bulletin_new/', include('apps.bulletin_new.urls')),
    path('payments/', include('apps.payments.urls')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('ckeditor/', include('ckeditor_uploader.urls')),
)

urlpatterns += [
    path('search/validate-query/', validate_query, name="validate_query"),
    path('search/get-task-info/', get_task_info, name="get_task_info"),
    path('search/toggle-search-form', toggle_search_form, name="toggle_search_form"),
    path('search/get-validation-info/', get_validation_info, name="get_validation_info"),
    path('api/', include('apps.api.urls')),
    path('paygate/', include('apps.paygate.urls')),
    path('favorites/add-or-remove', add_or_remove, name='favorites-add-or-remove'),
    # path('bulletin_new/get-applications/<int:bulletin_id>/<int:unit_id>/', get_applications),
    path('payments/api/orders', OrderCreateAPIView.as_view(), name='payments-orders'),
    path('payments/api/order/status/<int:pk>', OrderStatusAPIView.as_view(), name='payments-order-status')
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
