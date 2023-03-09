from dataclasses import dataclass


@dataclass
class InidCode:
    """Класс данных библиографического кода (код ИНИД)."""
    obj_type_id: int  # id типа ОПВ
    code: str  # код ИНИД
    title: str  # название поля
    obj_state: int  # статус объекта (1 - заявка, 2 - охранный документ)
    visible: bool  # признак видимости данных
