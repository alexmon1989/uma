from unittest import mock

from django.test import TestCase

from apps.search.services.application_data_receivers import create_service
from apps.search.models import IpcAppList, AppLimited, ObjType


class TestApplicationGetFullDataService(TestCase):
    databases = {'default', 'e_archive'}

    @mock.patch("apps.search.services.application_raw_data_fixers.cead_get_id_doc")
    def test_1(self, mock_cead_get_id_doc):
        mock_cead_get_id_doc.return_value = '12345'

        obj_type = ObjType(
            obj_type_ua='Торговельні марки'
        )
        obj_type.save()

        limited_app = AppLimited(
            app_number='m201918562',
            obj_type=obj_type,
        )
        limited_app.save()

        app = IpcAppList(
            app_number='m201918562',
            registration_number='307480',
            registration_date='2021-11-02',
            files_path='\\\\bear\\share\\TRADE_MARKS\\2019\\m201918562\\',
            obj_type=obj_type
        )

        service = create_service(app, 'filesystem')
        data = service.get_data()

        import json
        print(json.dumps(data))
