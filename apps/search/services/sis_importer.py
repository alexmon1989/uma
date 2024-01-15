from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from pathlib import Path
import json

from django.conf import settings

from apps.search.models import IpcAppList, FvCicImporter, ScheduleType


@dataclass
class Application:
    """Датакласс заявки."""
    ext_system_id: int  # id записи во внешней системе
    claim_id: int
    obj_type_id: int
    app_number: str
    app_input_date: datetime
    json_data: dict = None
    app_date: datetime = None
    reg_number: str = None
    reg_date: datetime = None
    files_path: Path = field(init=False, repr=True)

    def __post_init__(self):
        folders = {
            1: 'INVENTIONS',
            2: 'UTILITY_MOD',
            3: 'LAYOUT_DES',
            4: 'TRADE_MARKS',
            5: 'QUALIF_DESIGN',
            6: 'INDUSTRIAL_DES',
            9: 'MADRID_TM',
            10: 'CR/copyright',
            11: 'CR/agreement',
            12: 'CR/agreement',
            13: 'CR/copyright',
            14: 'MADRID_TM_REG_UA',
        }
        self.files_path = Path(settings.MEDIA_ROOT) \
                          / Path(folders[self.obj_type_id]) \
                          / str(self.app_input_date.year) \
                          / self.app_number


class SisImporter(ABC):
    """Сервис импорта данных заявок из внешних источников."""
    schedules: List[dict] = []

    @abstractmethod
    def get_applications(self) -> List[Application]:
        pass

    def _format_file_path_for_sis_db(self, path: Path) -> str:
        return str(path).replace(settings.MEDIA_ROOT, '\\\\bear\\share\\').replace('/', '\\') + '\\'

    def _get_application_schedule_id(self, application: Application) -> int | None:
        if not self.schedules:
            self.schedules = ScheduleType.objects.filter(
                pk__in=[3, 4, 5, 6, 7, 8, 16, 17, 18, 19, 30, 32, 10, 11, 12, 13, 14, 15]
            ).values('pk', 'obj_type_id')
        for item in self.schedules:
            if application.obj_type_id == item['obj_type_id']:
                # Охранный документ
                if application.reg_number and item['pk'] in [3, 4, 5, 6, 7, 8, 16, 17, 18, 19, 30, 32]:
                    return item['pk']
                # Заявка
                elif not application.reg_number and item['pk'] in [10, 11, 12, 13, 14, 15]:
                    return item['pk']
        return None

    def _process_application(self, application: Application) -> None:
        """Обрабатывает заявку"""
        # Запись в файловое хранилище
        application.files_path.mkdir(parents=True, exist_ok=True)
        file_path = application.files_path / f"{application.app_number}.json"
        with open(str(file_path), "w") as outfile:
            outfile.write(json.dumps(application.json_data))

        # Запись в БД СИС
        app_sis, created = IpcAppList.objects.update_or_create(
            app_number=application.app_number,
            obj_type_id=application.obj_type_id,
            registration_number=application.reg_number,
            defaults={
                'files_path': self._format_file_path_for_sis_db(application.files_path),
                'app_date': application.app_date,
                'app_input_date': application.app_input_date,
                'registration_date': application.reg_date,
                'elasticindexed': 0,
                'lastupdate': datetime.now(),
                'id_shedule_type': self._get_application_schedule_id(application),
                'id_parent': application.claim_id,
                'id_claim': application.claim_id,
            }
        )
        if not created:
            app_sis.changescount += 1
            app_sis.save()

    def execute(self) -> None:
        for app in self.get_applications():
            self._process_application(app)


class DenotationSisImporter(SisImporter):
    """Реализация сервиса импорта данных заявок из КАС Позначення."""
    type_code: str
    obj_type_id: int

    def _edit_json_data(self, app: Application) -> dict:
        """Редактирует JSON заявки."""
        app.json_data['Document']['filesPath'] = self._format_file_path_for_sis_db(app.files_path)
        return app.json_data

    def _process_application(self, application: Application) -> None:
        super()._process_application(application)

        # Пометка, что запись обработана
        FvCicImporter.objects.filter(
            id=application.ext_system_id
        ).using(
            'prod_erp_cms_import'
        ).update(
            is_exported='1',
            is_exported_datetime=datetime.now()
        )

    def get_applications(self) -> List[Application]:
        """Возвращает список заявок для индексации."""
        applications = FvCicImporter.objects.filter(
            is_exported=0,
            type_code=self.type_code
        ).order_by('id').using('prod_erp_cms_import')

        res = []
        for item in applications:
            application = Application(
                ext_system_id=item.id,
                obj_type_id=self.obj_type_id,
                app_number=item.claim_number,
                app_input_date=item.app_input_date,
                json_data=item.json_cic,
                app_date=item.app_set_date,
                reg_number=item.claim_od_number,
                reg_date=item.od_publication_date,
                claim_id=item.claim_id,
            )
            application.json_data = self._edit_json_data(application)
            res.append(application)
        return res


class GeoSisImporter(DenotationSisImporter):
    """Реализация сервиса импорта КЗПТ."""
    type_code = 'KZPT'
    obj_type_id = 5
