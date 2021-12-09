import tempfile
from EUSignCP import *
from django.conf import settings
import os, json


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
    except:
        pass

    # Выгрузка бибилиотек ІІТ
    eu_interface.Finalize()
    EUUnload()

    return sign_info
