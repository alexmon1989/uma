from django import forms
from django.contrib import admin
from apps.my_auth.models import KeyCenter, CertificateOwner, PatentAttorney
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class PatentAttorneyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PatentAttorneyForm, self).__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(
            groups__name='Патентні повірені'
        ).select_related('certificateowner')
        self.fields['user'].label_from_instance = lambda obj: "%s - %s %s" % (obj.username, obj.last_name, obj.first_name)


@admin.register(PatentAttorney)
class PatentAttorneyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'user_field',
        'created_at',
        'updated_at',
    )

    form = PatentAttorneyForm

    def get_queryset(self, request):
        """Переопределение списка параметров (отсекаются "вторые" реестры заявок)."""
        return PatentAttorney.objects.select_related('user').all()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = User.objects.filter(groups__name='Патентні повірені').select_related('certificateowner')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def user_field(self, obj):
        return f"{obj.user.username} - {obj.user.last_name} {obj.user.first_name}"

    user_field.short_description = "Користувач"


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


UserAdmin.search_fields = ('username', 'first_name', 'last_name', 'email', 'certificateowner__pszSubjFullName')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
