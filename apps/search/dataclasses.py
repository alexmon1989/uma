from dataclasses import dataclass


@dataclass
class InidCode:
    """Класс данных библиографического кода (код ИНИД)."""
    obj_type_id: int  # id типа ОПВ
    code: str  # код ИНИД
    title: str  # название поля
    obj_state: int  # статус объекта (1 - заявка, 2 - охранный документ)
    visible: bool  # признак видимости данных


@dataclass
class ApplicationDocument:
    """Датакласс документа заявки."""
    title: str  # название документа
    reg_number: str = None  # регистрационный номер документа
    id_doc_cead: int = None  # идентификатор ЦЕАД


@dataclass
class ServiceExecuteResultError:
    """Датакласс ошибки работы сервиса."""
    error_type: str
    message: str = None


@dataclass
class ServiceExecuteResult:
    """Датакласс результата работы сервиса."""
    status: str  # название документа
    error: ServiceExecuteResultError = None
    data: dict = None
