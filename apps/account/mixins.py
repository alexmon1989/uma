from django.http import Http404
from ..search.models import PaidServicesSettings


class PaidServicesEnabledMixin:
    """Verify that the current user is authenticated."""
    def dispatch(self, request, *args, **kwargs):
        paid_services_settings, created = PaidServicesSettings.objects.get_or_create()
        if not paid_services_settings.enabled:
            raise Http404()
        return super().dispatch(request, *args, **kwargs)
