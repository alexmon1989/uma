from datetime import datetime
from typing import Optional, Union

from django.core.cache import cache

from .models import ClListOfficialBulletinsIp


def bulletin_get_number_by_date(d: Union[datetime, str]) -> Optional[int]:
    """Возвращает номер бюллетеня для даты."""
    cache_key = f"bul_num_{d}"
    bul_number = cache.get(cache_key)
    if not bul_number:
        try:
            obj = ClListOfficialBulletinsIp.objects.get(date_from__lte=d, date_to__gte=d)
        except ClListOfficialBulletinsIp.DoesNotExist:
            return None
        else:
            bul_number = obj.bul_number
            cache.set(cache_key, bul_number, 3600)
    return bul_number


def bulletin_get_number_with_year_by_date(d: Union[datetime, str]) -> Optional[str]:
    """Возвращает номер бюллетеня с годом для даты."""
    cache_key = f"bul_num_with_year_{d}"
    bul_number = cache.get(cache_key)
    if not bul_number:
        try:
            obj = ClListOfficialBulletinsIp.objects.get(date_from__lte=d, date_to__gte=d)
        except ClListOfficialBulletinsIp.DoesNotExist:
            return None
        else:
            bul_number = f"{obj.bul_number}/{obj.bul_date.year}"
            cache.set(cache_key, bul_number, 3600)
    return bul_number
