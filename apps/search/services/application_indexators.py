from apps.search.models import IpcAppList
from apps.search.services.application_data_receivers import create_service as create_data_receiver_service
from apps.search.services.application_data_writers import create_service as create_data_writer_service


class ApplicationIndexationService:
    """Сервис для добавления информации о заявке в поисковый индекс."""

    _app: IpcAppList

    def __init__(self, app: IpcAppList):
        self._app = app

    def index(self) -> bool:
        # Получение данных
        data_receiver_service = create_data_receiver_service(self._app, 'filesystem')
        data = data_receiver_service.get_data()

        # Запись данных
        if data:
            data_writer_service = create_data_writer_service(self._app, data)
            data_writer_service.write()
            return True

        return False
