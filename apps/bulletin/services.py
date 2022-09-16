from datetime import datetime
from typing import Optional, Union

from django.core.cache import cache

from .models import ClListOfficialBulletinsIp


def bulletin_get_number_441_code(code_441_date: Union[datetime, str]) -> Optional[int]:
    """Возвращает номер бюллетеня для 441 кода."""
    cache_key = f"bul_num_{code_441_date}"
    bul_number = cache.get(cache_key)
    if not bul_number:
        try:
            obj = ClListOfficialBulletinsIp.objects.get(date_from__lte=code_441_date, date_to__gte=code_441_date)
        except ClListOfficialBulletinsIp.DoesNotExist:
            return None
        else:
            bul_number = obj.bul_number
            cache.set(cache_key, bul_number, 3600)
    return bul_number
