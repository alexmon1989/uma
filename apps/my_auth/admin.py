from django.contrib import admin
from apps.my_auth.models import KeyCenter, CertificateOwner

@admin.register(KeyCenter)
class KeyCenterAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'address',
        'ocspAccessPointAddress',
        'ocspAccessPointPort',
        'cmpAddress',
        'tspAddress',
        'tspAddressPort',
        'created_at',
        'updated_at',
    )

@admin.register(CertificateOwner)
class CertificateOwnerAdmin(admin.ModelAdmin):
    list_display = (
        'pszSerial',
        'user',
        'pszSubjFullName',
    )
    readonly_fields = (
        'pszIssuer',
        'pszIssuerCN',
        'pszSerial',
        'pszSubject',
        'pszSubjCN',
        'pszSubjOrg',
        'pszSubjOrgUnit',
        'pszSubjTitle',
        'pszSubjState',
        'pszSubjFullName',
        'pszSubjAddress',
        'pszSubjPhone',
        'pszSubjEMail',
        'pszSubjDNS',
        'pszSubjEDRPOUCode',
        'pszSubjDRFOCode',
        'pszSubjLocality',
    )
    search_fields = ('user__username', 'pszSerial', 'pszSubjFullName')
