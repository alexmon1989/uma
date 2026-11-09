from abc import ABC, abstractmethod
import base64
import json
import logging
import os
import re
import shutil
import urllib3
from typing import Any, List, Set
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import HttpResponse

from .models import CertificateOwner

try:
    from EUSignCP import EULoad, EUGetInterface, EUUnload, EU_INTERFACE
except ImportError:
    EULoad = EUGetInterface = EUUnload = None
    EU_INTERFACE = Any


logger = logging.getLogger(__name__)
UserModel = get_user_model()

VALID_AUTH_METHODS = ("file", "token", "password")


def get_enabled_auth_methods() -> list[str]:
    """Повертає список валідних увімкнених методів авторизації з налаштувань."""
    configured = getattr(settings, "AUTH_METHODS", VALID_AUTH_METHODS)
    if isinstance(configured, (list, tuple, set)):
        methods = [m for m in configured if m in VALID_AUTH_METHODS]
        return methods if methods else list(VALID_AUTH_METHODS)
    return list(VALID_AUTH_METHODS)


class UserService:

    @staticmethod
    def get_user_or_anonymous(user_id) -> UserModel | AnonymousUser:
        """Возвращает пользователя по его id или возвращает анонимного юзера, если он не найден."""
        try:
            user = UserModel.objects.prefetch_related("groups").get(id=user_id)
        except UserModel.DoesNotExist:
            user = AnonymousUser()

        return user

    @staticmethod
    def get_user_groups(user_id) -> List[str]:
        """Возвращает список групп пользователя."""
        user = UserModel.objects.filter(id=user_id).prefetch_related("groups").first()
        res = []
        for group in user.groups.all():
            res.append(group.name)
        return res


class IITProxyService:
    """
    Сервіс проксування HTTP/HTTPS-запитів до OCSP, TSP, CMP серверів АЦСК/КНЕДП
    для забезпечення роботи криптографічної бібліотеки ІІТ Користувач ЦСК (EndUser).
    Являє собою реалізацію на Python скрипта ProxyHandler.php від розробників бібліотек ІІТ
    """

    URL_MAX_LENGTH = 255
    URL_REGEX = re.compile(r"^(https?://)?([a-zA-Z0-9.\-]+)(:[0-9]{1,5})?(/.*)?$")

    DEFAULT_KNOWN_HOSTS = {
        "czo.gov.ua",
        "zc.bank.gov.ua",
        "acskidd.gov.ua",
        "ca.informjust.ua",
        "csk.uz.gov.ua",
        "masterkey.ua",
        "ocsp.masterkey.ua",
        "tsp.masterkey.ua",
        "csk.uss.gov.ua",
        "csk.ukrsibbank.com",
        "acsk.privatbank.ua",
        "ca.mil.gov.ua",
        "acsk.dpsu.gov.ua",
        "acsk.er.gov.ua",
        "ca.mvs.gov.ua",
        "canbu.bank.gov.ua",
        "uakey.com.ua",
        "altersign.com.ua",
        "ca.altersign.com.ua",
        "ocsp.altersign.com.ua",
        "acsk.treasury.gov.ua",
        "ocsp.treasury.gov.ua",
        "ca.oschadbank.ua",
        "ca.gp.gov.ua",
        "acsk.oree.com.ua",
        "ca.treasury.gov.ua",
        "ca.depositsign.com",
        "csk.pivdenny.ua",
        "xca.credit-agricole.com.ua",
        "ca.iit.com.ua",
        "ca.tascombank.com.ua",
        "ca.tascombank.ua",
        "ssign.diia.gov.ua",
        "depositsign.com",
        "pki.pumb.ua",
        "ca.alfabank.kiev.ua",
        "cesaris.itsway.kiev.ua",
        "ca.credit-agricole.ua",
        "csk-corp.aval.ua",
        "ca.e-life.com.ua",
        "ocsp.e-life.com.ua",
        "tsp.e-life.com.ua",
        "cmp.e-life.com.ua",
        "ca.bankalliance.ua",
        "ca.vchasno.ua",
        "qca.ukrgasbank.com",
        "ca.tax.gov.ua",
        "ca.diia.gov.ua",
        "ca.sensebank.com.ua",
        "va1-knedp.ssu.gov.ua",
        "ca.szru.gov.ua",
        "amokey.com.ua",
        "root-test.czo.gov.ua",
        "ca-test.czo.gov.ua",
        "apiext.pumb.ua",
    }

    CACHE_KEY_PREFIX = "iit_proxy_known_hosts"
    CACHE_TTL = 86400  # 24 години

    def __init__(self, request):
        self.request = request

    def _get_known_hosts(self) -> Set[str]:
        """Повертає повний набір дозволених хостів з кешуванням у Redis."""
        cas_path = os.path.join(settings.BASE_DIR, "certs", "CAs.json")
        file_mtime = int(os.path.getmtime(cas_path)) if os.path.exists(cas_path) else 0
        cache_key = f"{self.CACHE_KEY_PREFIX}:{file_mtime}"

        try:
            hosts = cache.get(cache_key)
            if hosts is not None:
                return hosts
        except Exception as e:
            logger.error(
                "Redis cache read failed for known hosts: %s", e, exc_info=True
            )
            hosts = None

        hosts = set(self.DEFAULT_KNOWN_HOSTS)
        if os.path.exists(cas_path):
            try:
                with open(cas_path, "r", encoding="utf-8") as f:
                    cas = json.load(f)
                for ca in cas:
                    for k in (
                        "address",
                        "ocspAccessPointAddress",
                        "cmpAddress",
                        "tspAddress",
                    ):
                        val = ca.get(k)
                        if val:
                            host = val.split("/")[0].split(":")[0].strip().lower()
                            if host:
                                hosts.add(host)
            except Exception as e:
                logger.error(
                    "Failed to load CAs.json for proxy whitelist: %s", e, exc_info=True
                )

        extra_hosts = getattr(settings, "EUSIGN_KNOWN_HOSTS", None)
        if extra_hosts:
            hosts.update(h.strip().lower() for h in extra_hosts)

        try:
            cache.set(cache_key, hosts, timeout=self.CACHE_TTL)
        except Exception as e:
            logger.error(
                "Redis cache write failed for known hosts: %s", e, exc_info=True
            )

        return hosts

    def _is_known_host(self, value: str) -> bool:
        """Перевіряє, чи є URL коректним і чи його хост присутній у списку довірених."""
        if not value or len(value) > self.URL_MAX_LENGTH:
            return False

        if not self.URL_REGEX.match(value):
            return False

        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https"):
            return False

        host = (parsed.hostname or "").lower()
        if not host:
            return False

        return host in self._get_known_hosts()

    def _get_content_type(self, value: str) -> str:
        """Визначає Content-Type вихідного запиту на основі шляху в URL."""
        path = urlparse(value).path or ""

        json_prefixes = (
            "/cloud/api/back/",
            "/ss/",
            "/api/EDG/Sign",
            "/smartid/iit/",
            "/hogsmeade/striga/v1",
            "/iit-signer/api/v1",
        )
        if any(prefix in path for prefix in json_prefixes):
            return "application/json"

        if path in (
            "/services/cmp",
            "/services/cmp/",
            "/public/x509/cmp",
            "/cmp",
            "/api/PKI/CMP",
        ):
            return ""

        ocsp_paths = (
            "/services/ocsp",
            "/services/ocsp/",
            "/public/ocsp",
            "/ocsp",
            "/ocsp-rsa",
            "/ocsp-ecdsa",
            "/OCSPsrv/ocsp",
            "/queries/ocsp/",
        )
        if path in ocsp_paths:
            return "application/ocsp-request"

        tsp_paths = (
            "/services/tsp",
            "/services/tsp/",
            "/services/tsp/dstu",
            "/services/tsp/dstu/",
            "/services/tsp/rsa",
            "/services/tsp/rsa/",
            "/services/tsp/ecdsa",
            "/services/tsp/ecdsa/",
            "/public/tsa",
            "/public/tsp",
            "/tsp",
            "/tsp-rsa",
            "/tsp-ecdsa",
            "/TspHTTPServer/tsp",
        )
        if path in tsp_paths:
            return "application/timestamp-query"

        return "text/plain"

    def _error_response(self, status_code: int = 400) -> HttpResponse:
        return HttpResponse(
            "Виникла помилка при обробці запиту",
            status=status_code,
            content_type="text/html; charset=utf-8",
        )

    def process(self) -> HttpResponse:
        """
        Головна публічна точка входу сервісу.
        Обробляє вхідний HTTP-запит і проксує його до відповідного АЦСК.
        Приймає base64-закодований POST-запит, надсилає сирі байти на цільовий сервер
        і повертає base64-закодовану відповідь з Content-Type: X-user/base64-data.
        """
        request = self.request

        if request.method not in ("GET", "POST"):
            return self._error_response(400)

        address = request.GET.get("address")
        if not address:
            return self._error_response(400)

        if not self._is_known_host(address):
            logger.warning("Proxy request rejected for unknown host: %s", address)
            return self._error_response(403)

        server_request = None
        if request.method == "POST":
            max_size = getattr(
                settings, "DATA_UPLOAD_MAX_MEMORY_SIZE", 10 * 1024 * 1024
            )
            if len(request.body) > max_size:
                return self._error_response(413)

            try:
                server_request = base64.b64decode(request.body)
            except Exception as e:
                logger.warning("Failed to decode base64 body: %s", e, exc_info=True)
                return self._error_response(400)

        headers = {
            "User-Agent": "signature.proxy",
        }
        content_type = self._get_content_type(address)
        if content_type:
            headers["Content-Type"] = content_type

        timeout = getattr(settings, "EUSIGN_PROXY_TIMEOUT", 30)
        verify_ssl = getattr(settings, "EUSIGN_PROXY_VERIFY_SSL", False)
        upstream_proxy = getattr(settings, "EUSIGN_UPSTREAM_PROXY", None)

        try:
            resp = requests.request(
                method=request.method,
                url=address,
                data=server_request,
                headers=headers,
                timeout=timeout,
                verify=verify_ssl,
                proxies=upstream_proxy,
            )
        except Exception as e:
            logger.error("Proxy request to %s failed: %s", address, e, exc_info=True)
            return self._error_response(500)

        if not resp.content:
            return self._error_response(500)

        encoded_response = base64.b64encode(resp.content).decode("ascii")

        response = HttpResponse(
            encoded_response,
            content_type="X-user/base64-data; charset=utf-8",
        )
        response["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response


class SignatureCheckService(ABC):
    """
    Абстрактний базовий клас для сервісів перевірки цифрового підпису (ЕЦП/КЕП).
    Визначає контракт для всіх криптографічних провайдерів (ІІТ, Дія.Підпис тощо).
    """

    @abstractmethod
    def get_signed_data_info(
        self, signed_data: str, secret: str, key_center_title: str
    ) -> dict[str, Any]:
        """
        Перевіряє валідність ЕЦП та повертає словник з інформацією про підпис.
        Повертає порожній словник у разі невалідності або помилки перевірки.
        """
        pass


class IITSignatureCheckService(SignatureCheckService):
    """
    Сервіс для роботи з криптографічною бібліотекою ІІТ Користувач ЦСК (EUSignCP).
    Забезпечує верифікацію цифрового підпису (ЕЦП/КЕП) та отримання даних підписувача.
    """

    def __init__(self):
        pass

    def _set_key_center_settings(
        self, eu_interface: EU_INTERFACE, key_center: dict[str, Any]
    ) -> None:
        """Встановлює параметри з'єднання з АЦСК для інтерфейсу ІІТ."""
        eu_interface.Initialize()
        filestore_path = getattr(
            settings, "EUSIGN_FILESTORE_PATH", os.path.join(settings.BASE_DIR, "certs")
        )
        ca_settings = {
            "szPath": filestore_path,
            "bCheckCRLs": False,
            "bAutoRefresh": True,
            "bOwnCRLsOnly": True,
            "bFullAndDeltaCRLs": True,
            "bAutoDownloadCRLs": True,
            "bSaveLoadedCerts": True,
            "dwExpireTime": 3600,
        }
        eu_interface.SetFileStoreSettings(ca_settings)

        ocsp_access_point_address = key_center.get("ocspAccessPointAddress", "")
        ca_settings = {
            "bUseOCSP": ocsp_access_point_address != "",
            "szAddress": ocsp_access_point_address,
            "bBeforeStore": True,
            "szPort": str(key_center.get("ocspAccessPointPort", "")),
        }
        eu_interface.SetOCSPSettings(ca_settings)

        tsp_address = key_center.get("tspAddress", "")
        ca_settings = {
            "bGetStamps": tsp_address != "",
            "szAddress": tsp_address,
            "szPort": str(key_center.get("tspAddressPort", "")),
        }
        eu_interface.SetTSPSettings(ca_settings)

        cmp_address = key_center.get("cmpAddress", "")
        ca_settings = {
            "bUseCMP": cmp_address != "",
            "szAddress": cmp_address,
            "szPort": "80",
            "szCommonName": "",
        }
        eu_interface.SetCMPSettings(ca_settings)

    def get_signed_data_info(
        self, signed_data: str, secret: str, key_center_title: str
    ) -> dict[str, Any]:
        """
        Головна публічна точка входу сервісу.
        Перевіряє валідність ЕЦП та повертає словник з інформацією про сертифікат підписувача.
        """
        if EULoad is None or EUGetInterface is None or EUUnload is None:
            logger.error("EUSignCP library is not available in the current environment")
            return {}

        # Завантаження бібліотеки ІІТ
        EULoad()
        eu_interface = EUGetInterface()
        eu_interface.Initialize()

        try:
            # Зчитування налаштувань центрів сертифікації з файлу CAs.json
            cas_path = os.path.join(settings.BASE_DIR, "certs", "CAs.json")
            if os.path.exists(cas_path):
                try:
                    with open(cas_path, "r", encoding="utf-8") as f:
                        key_centers = json.load(f)

                    # Застосування налаштувань центру сертифікації
                    for key_center in key_centers:
                        if key_center_title in key_center.get("issuerCNs", []):
                            self._set_key_center_settings(eu_interface, key_center)
                            break
                except Exception as e:
                    logger.error("Failed to load CAs.json: %s", e, exc_info=True)

            # Перевірка підпису
            p_data = secret.encode("utf-16-le")
            signed_data_bytes = signed_data.encode()
            sign_info = {}
            try:
                # Верифікація та отримання даних із підписаних даних
                eu_interface.VerifyData(
                    p_data,
                    len(p_data),
                    signed_data_bytes,
                    None,
                    len(signed_data_bytes),
                    sign_info,
                )
            except Exception as e:
                logger.error("VerifyData failed: %s", e, exc_info=True)

            return sign_info
        finally:
            # Гарантоване вивантаження бібліотеки ІІТ
            try:
                eu_interface.Finalize()
            except Exception as e:
                logger.error("Failed to finalize eu_interface: %s", e, exc_info=True)
            try:
                EUUnload()
            except Exception as e:
                logger.error("Failed to unload EUSignCP: %s", e, exc_info=True)


class CertificateService:
    """Сервіс для верифікації та отримання/створення записів CertificateOwner."""

    def __init__(self, signature_check_service: SignatureCheckService):
        self.signature_check_service = signature_check_service

    def get_or_create_from_signed_data(
        self, post_data: dict[str, Any], secret: str
    ) -> CertificateOwner | None:
        """Перевіряє ЕЦП за допомогою signature_service та повертає/створює CertificateOwner."""
        sign_info = self.signature_check_service.get_signed_data_info(
            signed_data=post_data.get("signed_data", ""),
            secret=secret,
            key_center_title=post_data.get("key_center_title", ""),
        )
        if not sign_info:
            return None

        key_type = post_data.get("key_type") or CertificateOwner.KEY_MEDIA_FILE
        if key_type not in (
            CertificateOwner.KEY_MEDIA_FILE,
            CertificateOwner.KEY_MEDIA_HARDWARE,
        ):
            key_type = CertificateOwner.KEY_MEDIA_FILE

        cert, created = CertificateOwner.objects.get_or_create(
            pszSerial=sign_info["pszSerial"],
            defaults={
                "key_media_type": key_type,
                "pszIssuer": sign_info.get("pszIssuer"),
                "pszIssuerCN": sign_info.get("pszIssuerCN"),
                "pszSubject": sign_info.get("pszSubject"),
                "pszSubjCN": sign_info.get("pszSubjCN"),
                "pszSubjOrg": sign_info.get("pszSubjOrg"),
                "pszSubjOrgUnit": sign_info.get("pszSubjOrgUnit"),
                "pszSubjTitle": sign_info.get("pszSubjTitle"),
                "pszSubjState": sign_info.get("pszSubjState"),
                "pszSubjFullName": sign_info.get("pszSubjFullName"),
                "pszSubjAddress": sign_info.get("pszSubjAddress"),
                "pszSubjPhone": sign_info.get("pszSubjPhone"),
                "pszSubjEMail": sign_info.get("pszSubjEMail"),
                "pszSubjDNS": sign_info.get("pszSubjDNS"),
                "pszSubjEDRPOUCode": sign_info.get("pszSubjEDRPOUCode"),
                "pszSubjDRFOCode": sign_info.get("pszSubjDRFOCode"),
                "pszSubjLocality": sign_info.get("pszSubjLocality"),
            },
        )
        if not created and cert.key_media_type != key_type:
            cert.key_media_type = key_type
            cert.save(update_fields=["key_media_type", "updated_at"])

        return cert


class CertsUpdateService:
    """
    Сервіс для автоматичного завантаження та оновлення файлів CAs.json та CACertificates.p7b
    з серверів, зазначених у налаштуваннях EUSIGN_CERTS_SOURCES.
    """

    DOWNLOAD_TIMEOUT = 60  # seconds
    MIN_P7B_SIZE_BYTES = 100 * 1024  # 100 KB
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }

    def __init__(
        self,
        certs_dir: str | None = None,
        sources: list[dict[str, str]] | None = None,
    ):
        self.certs_dir = certs_dir or getattr(
            settings, "EUSIGN_CERTS_DIR", os.path.join(settings.BASE_DIR, "certs")
        )
        self.sources = sources or getattr(settings, "EUSIGN_CERTS_SOURCES", [])

    def _download_file(self, url: str) -> bytes | None:
        """Завантажує файл за вказаним URL із контролем таймауту та налаштуванням перевірки SSL."""
        verify_ssl = getattr(settings, "EUSIGN_CERTS_VERIFY_SSL", False)
        try:
            if not verify_ssl:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            response = requests.get(
                url,
                headers=self.DEFAULT_HEADERS,
                timeout=self.DOWNLOAD_TIMEOUT,
                verify=verify_ssl,
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.warning("Failed to download %s: %s", url, e)
            return None

    def _validate_cas_json(self, content: bytes) -> bool:
        """Перевіряє коректність структури CAs.json."""
        try:
            data = json.loads(content.decode("utf-8"))
            if not isinstance(data, list) or len(data) == 0:
                logger.error("Validation failed: CAs.json is not a non-empty list")
                return False

            valid_items = sum(
                1
                for item in data
                if isinstance(item, dict) and "issuerCNs" in item and "address" in item
            )
            if valid_items < len(data) * 0.8:
                logger.error(
                    "Validation failed: CAs.json items missing issuerCNs or address"
                )
                return False

            return True
        except Exception as e:
            logger.error("Validation failed for CAs.json: %s", e)
            return False

    def _validate_p7b(self, content: bytes) -> bool:
        """Перевіряє коректність контейнера CACertificates.p7b."""
        if len(content) < self.MIN_P7B_SIZE_BYTES:
            logger.error(
                "Validation failed: CACertificates.p7b size is too small (%d bytes)",
                len(content),
            )
            return False

        # PKCS#7 у форматі DER починається з ASN.1 Sequence тегу 0x30
        if content[0] != 0x30:
            logger.error(
                "Validation failed: CACertificates.p7b is not a valid ASN.1 DER sequence"
            )
            return False

        return True

    def _save_file_safely(
        self, target_path: str, content: bytes, backup: bool = True
    ) -> bool:
        """
        Безпечно зберігає вміст у файл:
        1. Створює бекап існуючого файлу (.bak).
        2. Записує новий вміст у тимчасовий файл (.tmp).
        3. Атомарно замінює цільовий файл через os.replace.
        """
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            if backup and os.path.exists(target_path):
                backup_path = target_path + ".bak"
                shutil.copy2(target_path, backup_path)

            temp_path = target_path + ".tmp"
            with open(temp_path, "wb") as f:
                f.write(content)

            os.replace(temp_path, target_path)
            return True
        except Exception as e:
            logger.error(
                "Failed to safely save file %s: %s", target_path, e, exc_info=True
            )
            return False

    def update_certs(self, backup: bool = True) -> dict[str, Any]:
        """
        Головна точка входу для оновлення сертифікатів та списку ЦСК.
        Опитує джерела по черзі (primary -> fallback).
        Повертає словник зі статусом оновлення кожного файлу.
        """
        os.makedirs(self.certs_dir, exist_ok=True)
        results = {
            "success": False,
            "cas_updated": False,
            "p7b_updated": False,
            "source_used": None,
            "errors": [],
        }

        cas_target = os.path.join(self.certs_dir, "CAs.json")
        p7b_target = os.path.join(self.certs_dir, "CACertificates.p7b")

        if not self.sources:
            err_msg = (
                "No certificate sources configured in settings.EUSIGN_CERTS_SOURCES"
            )
            logger.error(err_msg)
            results["errors"].append(err_msg)
            return results

        for source in self.sources:
            source_name = source["name"]
            logger.info(
                "Attempting to download certificates from source: %s", source_name
            )

            # 1. Завантаження CAs.json
            cas_content = self._download_file(source["cas_url"])
            if not cas_content or not self._validate_cas_json(cas_content):
                err_msg = f"Source {source_name}: failed to obtain valid CAs.json"
                logger.warning(err_msg)
                results["errors"].append(err_msg)
                continue

            # 2. Завантаження CACertificates.p7b
            p7b_content = self._download_file(source["p7b_url"])
            if not p7b_content or not self._validate_p7b(p7b_content):
                err_msg = (
                    f"Source {source_name}: failed to obtain valid CACertificates.p7b"
                )
                logger.warning(err_msg)
                results["errors"].append(err_msg)
                continue

            # 3. Атомарне збереження обох файлів
            cas_saved = self._save_file_safely(cas_target, cas_content, backup=backup)
            p7b_saved = self._save_file_safely(p7b_target, p7b_content, backup=backup)

            if cas_saved and p7b_saved:
                results["cas_updated"] = True
                results["p7b_updated"] = True
                results["source_used"] = source_name
                results["success"] = True
                logger.info(
                    "Certificates and CAs.json successfully updated from source: %s",
                    source_name,
                )
                break
            else:
                err_msg = f"Source {source_name}: failed to write files to disk"
                results["errors"].append(err_msg)

        return results
