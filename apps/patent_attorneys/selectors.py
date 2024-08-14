from typing import Iterable

from django.db.models import Value
from django.db.models.functions import Concat

from .models import PatentAttorneyExt


def patent_attorney_list(name: str = None, reg_num: int = None, special: str = None, postal_address: str = None,
                         sort_by: str = None) -> Iterable[PatentAttorneyExt]:
    """Возвращает список патентных поверенных."""
    qs = PatentAttorneyExt.objects.all()

    # Сортировка
    if sort_by:
        sort_param = sort_by.split('_')
        direction = '' if sort_param[1] == 'asc' else '-'
        if sort_param[0] == 'regnum':
            qs = qs.order_by(f"{direction}reg_num")
        elif sort_param[0] == 'regdate':
            qs = qs.order_by(f"{direction}dat_reg")
        elif sort_param[0] == 'name':
            qs = qs.order_by(f"{direction}prizv", f"{direction}name", f"{direction}po_batk")

    # Фильтрация
    if name:
        qs = qs.annotate(search_name=Concat('prizv', Value(' '), 'name', Value(' '), 'po_batk'))
        qs = qs.filter(search_name__icontains=name)
    if reg_num:
        qs = qs.filter(reg_num=reg_num)
    if special:
        qs = qs.filter(special__icontains=special)
    if postal_address:
        qs = qs.annotate(search_address=Concat('postaladdress', Value(' '), 'phones', Value(' '), 'e_mail'))
        qs = qs.filter(search_address__icontains=postal_address)

    return qs
