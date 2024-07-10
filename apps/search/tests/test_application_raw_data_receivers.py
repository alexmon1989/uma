from django.test import TestCase

from unittest.mock import patch
import json

from apps.search.models import IpcAppList, AppLimited, ObjType
from apps.search.services.application_raw_data_receivers import (ApplicationRawDataFSReceiver,
                                                                 ApplicationRawDataFSMadridReceiver,
                                                                 ApplicationRawDataFSTMReceiver,
                                                                 ApplicationRawDataReceiver,
                                                                 ApplicationRawDataFSIDReceiver,
                                                                 ApplicationRawDataFSInvUMLDReceiver)
from apps.bulletin.models import EBulletinData, ClListOfficialBulletinsIp


class ApplicationRawDataFSReceiverTestCase(TestCase):
    """Тестирует класс ApplicationRawDataFSReceiver."""

    def test_is_instance(self):
        receiver = ApplicationRawDataFSReceiver(IpcAppList())
        self.assertIsInstance(receiver, ApplicationRawDataReceiver)

    def test_set_file_path(self):
        app = IpcAppList()
        app.files_path = '/tmp/app.json'
        receiver = ApplicationRawDataFSReceiver(app)
        receiver._set_file_path()
        self.assertEqual(receiver._file_path, app.files_path)

        app = IpcAppList()
        app.registration_number = 'reg/number'
        app.app_number = 'app_number'
        app.files_path = '/tmp/'
        receiver = ApplicationRawDataFSReceiver(app)
        receiver._set_file_path()
        self.assertEqual(receiver._file_path, '/tmp/reg_number.json')

        app = IpcAppList()
        app.registration_number = '0'
        app.app_number = 'app_number'
        app.files_path = '/tmp/'
        receiver = ApplicationRawDataFSReceiver(app)
        receiver._set_file_path()
        self.assertEqual(receiver._file_path, '/tmp/app_number.json')

        app = IpcAppList()
        app.app_number = 'app_number'
        app.files_path = '/tmp/'
        receiver = ApplicationRawDataFSReceiver(app)
        receiver._set_file_path()
        self.assertEqual(receiver._file_path, '/tmp/app_number.json')

        for obj_type_id in (4, 5, 6):
            app = IpcAppList()
            app.obj_type_id = obj_type_id
            app.registration_number = 'reg_num'
            app.app_number = 'app/number'
            app.files_path = '/tmp/'
            receiver = ApplicationRawDataFSReceiver(app)
            receiver._set_file_path()
            self.assertEqual(receiver._file_path, '/tmp/app_number.json')

    def test_get_data(self):
        obj_type = ObjType.objects.create(obj_type_ua='Винаходи')
        test_data = {
            'Document': {'idObjType': obj_type.pk}
        }
        with open('/tmp/app.json', 'w') as fp:
            json.dump(test_data, fp)

        app = IpcAppList()
        app.obj_type_id = 1
        app.app_number = 'app'
        app.files_path = '/tmp/'
        receiver = ApplicationRawDataFSReceiver(app)
        data = receiver.get_data()
        self.assertEqual(data['Document']['idObjType'], obj_type.pk)
        self.assertFalse(data['Document']['is_limited'])

        AppLimited.objects.create(obj_type_id=obj_type.pk, app_number='app')
        data = receiver.get_data()
        self.assertTrue(data['Document']['is_limited'])


class ApplicationRawDataFSTMReceiverTestCase(TestCase):
    def test_is_instance(self):
        receiver = ApplicationRawDataFSTMReceiver(IpcAppList())
        self.assertIsInstance(receiver, ApplicationRawDataFSReceiver)

    def test_get_data(self):
        obj_type = ObjType.objects.create(obj_type_ua='Торговельні марки')

        test_data = {
            'Document': {'idObjType': obj_type.pk},
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicationNumber': 'm202400001'
                }
            }
        }
        with open('/tmp/m202400001.json', 'w') as fp:
            json.dump(test_data, fp)
        app = IpcAppList.objects.create(
            app_number='m202400001', files_path='/tmp/', obj_type_id=obj_type.pk, id_shedule_type=1
        )

        receiver = ApplicationRawDataFSTMReceiver(app)
        data = receiver.get_data()
        self.assertNotIn('Code_441', data['TradeMark']['TrademarkDetails'])

        EBulletinData.objects.create(app_number='m202400001', publication_date='2024-07-04')
        data = receiver.get_data()
        self.assertEqual(data['TradeMark']['TrademarkDetails']['Code_441'], '2024-07-04')

        # Значение 441 из файла имеет преимущество
        test_data['TradeMark']['TrademarkDetails']['Code_441'] = '2024-01-01'
        with open('/tmp/m202400001.json', 'w') as fp:
            json.dump(test_data, fp)
        data = receiver.get_data()
        self.assertEqual(data['TradeMark']['TrademarkDetails']['Code_441'], '2024-01-01')


class ApplicationRawDataFSIDReceiverTestCase(TestCase):
    def test_is_instance(self):
        receiver = ApplicationRawDataFSIDReceiver(IpcAppList())
        self.assertIsInstance(receiver, ApplicationRawDataFSReceiver)


class ApplicationRawDataFSInvUMLDReceiverTestCase(TestCase):
    def test_is_instance(self):
        receiver = ApplicationRawDataFSInvUMLDReceiver(IpcAppList())
        self.assertIsInstance(receiver, ApplicationRawDataFSReceiver)

    def test_set_i_43_bul_str(self):
        with open('/tmp/a202400001.json', 'w') as fp:
            json.dump({'Claim': {'I_43.D': ['2024-07-09']}}, fp)
        app = IpcAppList(app_number='a202400001', files_path='/tmp/')
        ClListOfficialBulletinsIp.objects.create(bul_date='2024-07-09', bul_number=7)
        receiver = ApplicationRawDataFSInvUMLDReceiver(app)
        data = receiver.get_data()
        self.assertEqual(data['Claim']['I_43_bul_str'], '7/2024')

    def test_set_i_45_bul_str(self):
        with open('/tmp/11111.json', 'w') as fp:
            json.dump({
                'Patent': {
                    'I_45.D': ['2024-07-09'],
                    'I_43.D': ['2024-01-01']
                }
            }, fp)
        app = IpcAppList(app_number='a202400001', registration_number='11111', files_path='/tmp/')
        ClListOfficialBulletinsIp.objects.create(bul_date='2024-07-09', bul_number=7)
        ClListOfficialBulletinsIp.objects.create(bul_date='2024-01-01', bul_number=1)
        receiver = ApplicationRawDataFSInvUMLDReceiver(app)
        data = receiver.get_data()
        self.assertEqual(data['Patent']['I_45_bul_str'], '7/2024')
        self.assertEqual(data['Patent']['I_43_bul_str'], '1/2024')


class ApplicationRawDataFSMadridReceiverTestCase(TestCase):

    @patch('apps.search.services.application_raw_data_receivers.ApplicationRawDataFSMadridReceiver._set_450')
    def test_set_450(self, mock_set_450):

        def side_effect(d: dict):
            d['a'] = 'b'

        mock_set_450.side_effect = side_effect
        app = IpcAppList(obj_type_id=9)
        receiver = ApplicationRawDataFSMadridReceiver(app)
        data = {}
        receiver._set_450(data)
        self.assertEqual(data['a'], 'b')
