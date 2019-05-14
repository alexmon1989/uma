import tempfile
from EUSignCP import *
from django.conf import settings
import os


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

    ca_settings = {
        'bUseOCSP': key_center.ocspAccessPointAddress is not None and key_center.ocspAccessPointAddress != '',
        'szAddress': key_center.ocspAccessPointAddress or '',
        'bBeforeStore': True,
        'szPort': str(key_center.ocspAccessPointPort),
    }
    eu_interface.SetOCSPSettings(ca_settings)

    ca_settings = {
        'bGetStamps': key_center.tspAddress is not None and key_center.tspAddress != '',
        'szAddress': key_center.tspAddress or '',
        'szPort': str(key_center.tspAddressPort),
    }
    eu_interface.SetTSPSettings(ca_settings)

    ca_settings = {
        'bUseCMP': key_center.cmpAddress is not None and key_center.cmpAddress != '',
        'szAddress': key_center.cmpAddress or '',
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
