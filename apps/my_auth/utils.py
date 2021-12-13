import tempfile
from EUSignCP import *
from django.conf import settings
from .models import CertificateOwner
import os
import json
import logging

logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)


def set_key_center_settings(eu_interface, key_center):
    """Устанавливает параметры соединения с АЦСК"""
    eu_interface.Initialize()
    ca_settings = {
        'szPath': settings.EUSIGN_FILESTORE_PATH,
        'bCheckCRLs': True,
        'bAutoRefresh': True,
        'bOwnCRLsOnly': False,
        'bFullAndDeltaCRLs': True,
        'bAutoDownloadCRLs': True,
        'bSaveLoadedCerts': True,
        'dwExpireTime': 3600,
    }
    eu_interface.SetFileStoreSettings(ca_settings)

    ocspAccessPointAddress = key_center.get('ocspAccessPointAddress', '')
    ca_settings = {
        'bUseOCSP': ocspAccessPointAddress != '',
        'szAddress': ocspAccessPointAddress,
        'bBeforeStore': True,
        'szPort': str(key_center['ocspAccessPointPort']),
    }
    eu_interface.SetOCSPSettings(ca_settings)

    tspAddress = key_center.get('tspAddress')
    ca_settings = {
        'bGetStamps': tspAddress != '',
        'szAddress': tspAddress,
        'szPort': str(key_center.get('tspAddressPort', '')),
    }
    eu_interface.SetTSPSettings(ca_settings)

    cmpAddress = key_center.get('cmpAddress', '')
    ca_settings = {
        'bUseCMP': cmpAddress != '',
        'szAddress': cmpAddress,
        'szPort': '80',
        'szCommonName': '',
    }
    eu_interface.SetCMPSettings(ca_settings)


def get_certificate_data(file_path, password, key_center):
    """Возвращает данные сертификата ЭЦП."""
    # Загрузка библиотеки ЭЦП
    EULoad()
    eu_interface = EUGetInterface()
    set_key_center_settings(eu_interface, key_center)
    eu_interface.Initialize()
    cert_info = {}
    eu_interface.ReadPrivateKeyFile(file_path, password, cert_info)
    eu_interface.Finalize()
    EUUnload()
    cert_info.pop('bFilled')
    return cert_info


def save_file_to_temp(file):
    """Сохраняет файл во временный каталог ОС."""
    handle, path = tempfile.mkstemp()
    with open(handle, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    return path


def save_file_to_eu_file_store(file):
    """Сохраняет файл во файловое хранилище библиотек ЭЦП."""
    path = os.path.join(settings.EUSIGN_FILESTORE_PATH, file.name)
    with open(path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    return path


def get_signed_data_info(signed_data, secret, key_center_title):
    """Вроверяет валидность ЭЦП."""
    # Загрузка бибилиотек ІІТ
    EULoad()
    pIface = EUGetInterface()
    pIface.Initialize()
    eu_interface = EUGetInterface()

    # Считывание настроек центров сертификации из файла CAs.json
    key_centers = open(os.path.join(settings.BASE_DIR, 'apps', 'my_auth', 'static', 'my_auth', 'CAs.json'), "r").read()
    key_centers = json.loads(key_centers)

    # Применение настроек центра сертификации
    for key_center in key_centers:
        if key_center_title in key_center['issuerCNs']:
            set_key_center_settings(eu_interface, key_center)
            break

    # Проверка подписи
    pData = secret.encode('utf-16-le')
    signed_data = signed_data.encode()
    sign_info = {}
    try:
        # Верификация и получение данных из подписанных данных
        pIface.VerifyData(pData, len(pData), signed_data, None, len(signed_data), sign_info)
    except Exception as e:
        logger.error(e)

    # Выгрузка бибилиотек ІІТ
    eu_interface.Finalize()
    EUUnload()

    return sign_info


def get_certificate(post_data, secret):
    """Возвращает сертификат ЭЦП."""
    if settings.VALIDATE_DS and not post_data['serial'] in settings.VALIDATE_DS_WHITE_LIST_CERTS:
        # Проверка валидности ЭЦП
        sign_info = get_signed_data_info(post_data['signed_data'],
                                         secret,
                                         post_data['key_center_title'])
        if not sign_info:
            # Проверка закончилась неудачей
            return None
        else:
            try:
                cert = CertificateOwner.objects.get(pszSerial=sign_info['pszSerial'])
            except CertificateOwner.DoesNotExist:
                # Запись данных ключа в БД
                cert = CertificateOwner(
                    pszIssuer=sign_info.get('pszIssuer'),
                    pszIssuerCN=sign_info.get('pszIssuerCN'),
                    pszSerial=sign_info.get('pszSerial'),
                    pszSubject=sign_info.get('pszSubject'),
                    pszSubjCN=sign_info.get('pszSubjCN'),
                    pszSubjOrg=sign_info.get('pszSubjOrg'),
                    pszSubjOrgUnit=sign_info.get('pszSubjOrgUnit'),
                    pszSubjTitle=sign_info.get('pszSubjTitle'),
                    pszSubjState=sign_info.get('pszSubjState'),
                    pszSubjFullName=sign_info.get('pszSubjFullName'),
                    pszSubjAddress=sign_info.get('pszSubjAddress'),
                    pszSubjPhone=sign_info.get('pszSubjPhone'),
                    pszSubjEMail=sign_info.get('pszSubjEMail'),
                    pszSubjDNS=sign_info.get('pszSubjDNS'),
                    pszSubjEDRPOUCode=sign_info.get('pszSubjEDRPOUCode'),
                    pszSubjDRFOCode=sign_info.get('pszSubjDRFOCode'),
                    pszSubjLocality=sign_info.get('pszSubjLocality'),
                )
                cert.save()
    else:
        try:
            cert = CertificateOwner.objects.get(pszSerial=post_data['serial'])
        except CertificateOwner.DoesNotExist:
            # Запись данных ключа в БД
            cert = CertificateOwner(
                pszIssuer=post_data['issuer'],
                pszIssuerCN=post_data['issuerCN'],
                pszSerial=post_data['serial'],
                pszSubject=post_data['subject'],
                pszSubjCN=post_data['subjCN'],
                pszSubjOrg=post_data['subjOrg'],
                pszSubjOrgUnit=post_data['subjOrgUnit'],
                pszSubjTitle=post_data['subjTitle'],
                pszSubjState=post_data['subjState'],
                pszSubjFullName=post_data['subjFullName'],
                pszSubjAddress=post_data['subjAddress'],
                pszSubjPhone=post_data['subjPhone'],
                pszSubjEMail=post_data['subjEMail'],
                pszSubjDNS=post_data['subjDNS'],
                pszSubjEDRPOUCode=post_data['subjEDRPOUCode'],
                pszSubjDRFOCode=post_data['subjDRFOCode'],
                pszSubjLocality=post_data['subjLocality'],
            )
            cert.save()

    return cert
