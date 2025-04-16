from datetime import datetime
from typing import Optional, Union

from django.core.cache import cache
from django.db.models import Q

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
        obj = ClListOfficialBulletinsIp.objects.filter(Q(date_from__lte=d, date_to__gte=d) | Q(bul_date=d)).first()
        if obj:
            bul_number = f"{obj.bul_number}/{obj.bul_date.year}"
            cache.set(cache_key, bul_number, 3600)
        else:
            return None
    return bul_number


def bulletin_get_date_by_num_and_year(num: int, year: int) -> str | None:
    """Повертає дату бюлетеня по його номеру та року."""
    cache_key = f"bul_date_{num}_{year}"
    bul_date = cache.get(cache_key)
    if bul_date:
        return bul_date

    obj = ClListOfficialBulletinsIp.objects.filter(bul_number=num, bul_date__year=year).first()
    if obj:
        bul_date = obj.bul_date.strftime('%Y-%m-%d')
        cache.set(cache_key, bul_date, 3600)
        return bul_date

    cache.set(cache_key, None, 3600)
    return None
