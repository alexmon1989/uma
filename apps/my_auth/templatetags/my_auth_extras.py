from django import template
from apps.my_auth.models import CertificateOwner

register = template.Library()

@register.simple_tag
def cert_owner_fullname(user):
    """Возвращает имя владельца сертификата."""
    if user.is_staff:
        return user.username
    cert = CertificateOwner.objects.get(user=user)
    return cert.pszSubjFullName
