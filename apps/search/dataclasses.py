from dataclasses import dataclass


@dataclass
class InidCode:
    """Класс для определения видим ли библиографический код (код ИНИД)."""
    code: str  # код ИНИД
    title: str  # название поля
    obj_state: int  # статус объекта (1 - заявка, 2 - охранный документ)
    visible: bool  # признак видимости данных
