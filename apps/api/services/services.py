from django.db.models import F
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from apps.search.models import IpcAppList
from apps.api.models import OpenData
from typing import List, Optional, Union


def app_get_api_list(options: dict) -> List:
    """Возвращает список объектов для добавления в API"""
    apps = IpcAppList.objects.filter(
        elasticindexed=1
    ).exclude(
        obj_type_id__in=(1, 2, 3, 5), registration_date__isnull=True
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
