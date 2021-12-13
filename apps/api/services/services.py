from django.db.models import F
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from apps.search.models import IpcAppList
from apps.api.models import OpenData
from apps.bulletin.models import EBulletinData
from typing import List, Optional, Union
from datetime import datetime


def app_get_api_list(options: dict) -> List:
    """Возвращает список объектов для добавления в API"""
    apps = IpcAppList.objects.filter(
        elasticindexed=1
    ).exclude(
        obj_type_id__in=(5,), registration_date__isnull=True
    ).exclude(
        obj_type_id__in=(9, 14)
    ).annotate(
        app_id=F('id'), last_update=F('lastupdate')
    ).values_list('app_id', 'last_update')

    # Объекты в API
    api_apps = OpenData.objects.values_list('app_id', 'last_update')

    # Фильтр по параметру id (если в API нужно добавить только определённую заявку)
    if options['id']:
        apps = apps.filter(id=options['id'])
        api_apps = api_apps.filter(app_id=options['id'])

    # Фильтр по типу объекта
    if options['obj_type_ids']:
        apps = apps.filter(obj_type_id__in=options['obj_type_ids'])
        api_apps = api_apps.filter(obj_type_id__in=options['obj_type_ids'])

    # Объекты, которых нет в API (или которые имеют другое значение поля last_update)
    if options['not_compare_last_update']:
        diff = apps
    else:
        diff = list(set(apps) - set(api_apps))

    return diff


def app_get_claim_from_es(app_number: str) -> dict:
    """Возвращает данные заявки (search_data.obj_state:1) из ES."""
    es = Elasticsearch(settings.ELASTIC_HOST, timeout=settings.ELASTIC_TIMEOUT)
    claim = Search(
        using=es,
        index=settings.ELASTIC_INDEX_NAME
    ).query(
        Q(
            'query_string',
            query=f"search_data.obj_state:1 AND search_data.app_number:{app_number}"
        )
    ).source(
        excludes=["*.DocBarCode", "*.DOCBARCODE"]
    ).execute()
    if claim:
        return claim[0].to_dict()
    return {}


def app_get_payments(app_data: dict) -> Optional[Union[dict, List]]:
    """Возвращает платежи по заявке"""
    # Платежи по изобретениям, полезным моделям, топографиям
    if app_data['Document']['idObjType'] in (1, 2, 3):
        res = {
            'payments': app_data.get('DOCFLOW', {}).get('PAYMENTS', []),
            'collections': app_data.get('DOCFLOW', {}).get('COLLECTIONS', []),
        }

        # Если это охранный документ, то необходимо объеденить с платежами по заявке
        if app_data['search_data']['obj_state'] == 2:
            claim = app_get_claim_from_es(app_data['search_data']['app_number'])
            if claim:
                if claim.get('DOCFLOW', {}).get('PAYMENTS'):
                    res['payments'].extend(claim['DOCFLOW']['PAYMENTS'])
                if claim.get('DOCFLOW', {}).get('COLLECTIONS'):
                    res['collections'].extend(claim['DOCFLOW']['COLLECTIONS'])

        return res

    # Платежи по ТМ
    elif app_data['Document']['idObjType'] == 4:
        return app_data.get('TradeMark', {}).get('PaymentDetails')

    # Платежи по пром. образцам
    elif app_data['Document']['idObjType'] == 6:
        return app_data.get('Design', {}).get('PaymentDetails')

    # По другим объектам платежей пока нет
    else:
        return None


def app_get_documents(app_data: dict) -> Optional[Union[dict, List]]:
    """Возвращает документы по заявке."""
    # Документы по изобретениям, полезным можелям, топографиям
    if app_data['Document']['idObjType'] in (1, 2, 3):
        res = app_data.get('DOCFLOW', {}).get('DOCUMENTS', [])

        # Если это охранный документ, то необходимо объеденить с документами по заявке
        if app_data['search_data']['obj_state'] == 2:
            claim = app_get_claim_from_es(app_data['search_data']['app_number'])
            if claim and claim.get('DOCFLOW', {}).get('DOCUMENTS'):
                res.extend(claim['DOCFLOW']['DOCUMENTS'])

        if res:
            return res
        else:
            return None

    # Документы по ТМ
    elif app_data['Document']['idObjType'] == 4:
        return app_data['TradeMark'].get('DocFlow', {}).get('Documents')

    # Документы по пром. образцам
    elif app_data['Document']['idObjType'] == 6:
        return app_data['Design'].get('DocFlow', {}).get('Documents')

    # Документы по пром. образцам
    elif app_data['Document']['idObjType'] in (10, 13):
        return app_data['Certificate']['CopyrightDetails'].get('DocFlow', {}).get('Documents')

    # Документы по пром. образцам
    elif app_data['Document']['idObjType'] in (11, 12):
        return app_data['Decision']['DecisionDetails'].get('DocFlow', {}).get('Documents')

    # По другим объектам документов пока нет
    else:
        return None


def app_get_biblio_data(app_data: dict) -> Optional[dict]:
    """Возвращает библиографические данные заявки."""
    # Библ. данные заявок на полезные модели и топографии не публикуются
    if app_data['Document']['idObjType'] in (1, 3) and app_data['search_data']['obj_state'] == 1:
        data_biblio = None

    # Библ. данные по изобретениям, полезным можелям, топографиям
    elif app_data['Document']['idObjType'] in (1, 2, 3):
        data_biblio = app_data.get('Patent', app_data.get('Claim'))

    # Свидетельства на знаки для товаров и услуг
    elif app_data['Document']['idObjType'] == 4:
        can_be_published = True  # Может ли заявка быть опубликована
        data_biblio = {}

        if app_data['TradeMark']['TrademarkDetails'].get('Code_441') is None:
            # Поле 441 (дата опубликования заявки)
            e_bulletin_app = EBulletinData.objects.filter(
                app_number=app_data['TradeMark']['TrademarkDetails']['ApplicationNumber']
            ).first()
            if e_bulletin_app:
                # 441 код найден - заявка может публиковаться
                code_441 = str(e_bulletin_app.publication_date)
                data_biblio['Code_441'] = code_441
            else:
                # Если это заявка
                if app_data['search_data']['obj_state'] == 1:
                    # и её дата подачи после 18.07.2020, то публиковать её нельзя
                    app_date = app_data['TradeMark']['TrademarkDetails'].get('ApplicationDate')
                    if not app_date \
                            or datetime.strptime(app_date[:10], '%Y-%m-%d') > datetime.strptime('2020-07-17', '%Y-%m-%d'):
                        can_be_published = False

        if can_be_published:
            data_biblio.update(app_data['TradeMark']['TrademarkDetails'])

            if app_data['search_data']['obj_state'] == 1:
                # Статус заявки
                mark_status_code = int(app_data['Document'].get('MarkCurrentStatusCodeType', 0))
                is_stopped = app_data['Document'].get(
                    'RegistrationStatus') == 'Діловодство за заявкою припинено' or mark_status_code == 8000
                if is_stopped:
                    data_biblio['application_status'] = 'stopped'
                else:
                    data_biblio['application_status'] = 'active'
        else:
            data_biblio = None

    # Свидетельства на КЗПТ
    elif app_data['Document']['idObjType'] == 5:
        data_biblio = app_data['Geo']['GeoDetails']

    # Патенты на пром. образцы
    elif app_data['Document']['idObjType'] == 6:
        # Записывается только библиография патентов
        data_biblio = app_data['Design']['DesignDetails'] if app_data['search_data']['obj_state'] == 2 else None
        data_biblio = data_biblio

    # Авторське право
    elif app_data['Document']['idObjType'] in (10, 13):
        if app_data['Certificate']['CopyrightDetails'].get('DocFlow'):
            del app_data['Certificate']['CopyrightDetails']['DocFlow']
        data_biblio = app_data['Certificate']['CopyrightDetails']

    # Авторське право (договора)
    elif app_data['Document']['idObjType'] in (11, 12):
        if app_data['Decision']['DecisionDetails'].get('DocFlow'):
            del app_data['Decision']['DecisionDetails']['DocFlow']
        data_biblio = app_data['Decision']['DecisionDetails']

    else:
        data_biblio = None

    if app_data['search_data']['obj_state'] == 2 and data_biblio:
        data_biblio['registration_status_color'] = app_data['search_data']['registration_status_color']

    return data_biblio
