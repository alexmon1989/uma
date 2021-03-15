from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.http import JsonResponse, Http404
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import *
from .utils import get_bulletins, get_bulletin_tree, fix_data_inv_um, fix_data_id, fix_data_tm, prepare_madrid_tm_data
from apps.search.models import InidCodeSchedule, AppDocuments
import json


def get_applications(request, bulletin_id, unit_id):
    """Возвращает JSON со списком заявок"""
    bulletin = get_object_or_404(Bulletin, pk=bulletin_id)
    apps = EBulletinData.objects.filter(
        unit_id=unit_id,
        publication_date=bulletin.bul_date
    ).order_by('registration_number', 'app_number')

    res = []
    for app in apps:
        res.append({
            'id': app.id,
            'name': app.registration_number if app.registration_number and app.registration_number != '0' else app.app_number,
        })

    return JsonResponse(res, safe=False)


class IndexView(TemplateView):

    template_name = 'bulletin_new/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['bulletins'] = get_bulletins()

        if self.request.GET.get('bulletin_date'):
            context['tree'] = get_bulletin_tree(self.request.GET['bulletin_date'])
        else:
            context['tree'] = []

        return context


class AppDetailView(DetailView):
    """Возвращает HTML заявки."""
    model = EBulletinData
    template_name = 'bulletin_new/detail/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Данные заявки
        context['app_data'] = json.loads(self.object.json_data[:len(self.object.json_data)-1])

        # У изобретений и полезных моделей библиографические данные находятся в разных секциях
        if self.object.unit.obj_type.pk in (1, 2):
            context['app_data']['biblio_data'] = context['app_data'].get('Claim', context['app_data'].get('Patent', {}))
            fix_data_inv_um(context['app_data']['biblio_data'])

            # Путь к документу формулы
            try:
                context['app_data']['cl'] = self.object.app.appdocuments_set.get(
                    enter_num=98, file_type='pdf'
                ).file_name.replace("\\\\bear\share\\", settings.MEDIA_URL).replace("\\", "/")
            except AppDocuments.DoesNotExist:
                pass

        elif self.object.unit.obj_type.pk == 4:
            fix_data_tm(context['app_data'])
        elif self.object.unit.obj_type.pk == 6:
            fix_data_id(context['app_data'])
        elif self.object.unit.obj_type.pk in (9, 14):
            prepare_madrid_tm_data(context['app_data'], self.object)

        # Видимость полей библиографических данных
        context['lang_code'] = 'ua' if self.request.LANGUAGE_CODE == 'uk' else 'en'
        ipc_fields = InidCodeSchedule.objects.filter(
            ipc_code__obj_types=self.object.unit.obj_type
        ).annotate(
            code_title=F(f"ipc_code__code_value_{context['lang_code']}"),
            ipc_code_short=F('ipc_code__code_inid')
        ).values('ipc_code_short', 'code_title', 'enable_view')
        if self.object.registration_number:  # Охранный документ или заявка
            ipc_fields = ipc_fields.filter(
                Q(schedule_type__id__gte=3, schedule_type__id__lte=8) | Q(schedule_type__id=32)
            )
        else:
            ipc_fields = ipc_fields.filter(
                Q(schedule_type__id__gte=9, schedule_type__id__lte=15) | Q(schedule_type__id=30)
            )
        context['ipc_fields'] = ipc_fields

        return context

    def get_template_names(self):
        template = 'bulletin_new/detail/index.html'

        # Відомості про заявки на винаходи, що містять бібліографічні дані
        # Відомості про державну реєстрацію винаходів
        # Відомості про державну реєстрацію корисних моделей
        if self.object.unit.obj_type.pk in (1, 2):
            template = 'bulletin_new/detail/inv.html'

        # Відомості про державну реєстрацію компонувань напівпровідникових виробів

        # Відомості про заявки на торговельні марки
        # Відомості про видачу свідоцтв України на торговельні марки
        elif self.object.unit.obj_type.pk == 4:
            template = 'bulletin_new/detail/tm.html'

        # Відомості про державну реєстрацію промислових зразків
        elif self.object.unit.obj_type.pk == 6:
            template = 'bulletin_new/detail/id.html'

        # Відомості про торговельні марки, зареєстровані відповідно до Протоколу до Мадридської угоди про міжнародну
        # реєстрацію знаків, з поширенням на територію України
        # Відомості про торговельні марки, зареєстровані відповідно до Протоколу до Мадридської угоди про міжнародну
        # реєстрацію знаків, яким надана охорона в Україні
        elif self.object.unit.obj_type.pk in (9, 14):
            template = 'bulletin_new/detail/tm_madrid.html'

        return (template, )


class TransactionsView(TemplateView):
    """Отобрадает оповещения определенного бюлетня определённого типа."""
    template_name = 'bulletin_new/transactions/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bul_id = kwargs.get('bul_id')
        transaction_type_id = kwargs.get('transaction_type_id')

        try:
            context['transaction_type'] = TransactionType.objects.get(pk=transaction_type_id)
        except TransactionType.DoesNotExist:
            raise Http404()

        context['transactions'] = Transaction.objects.filter(
            bulletin__pk=bul_id,
            transaction_type__pk=transaction_type_id
        ).select_related('application')

        return context
