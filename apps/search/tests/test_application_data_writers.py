import datetime
import json
import os
import shutil
from unittest import mock

from django.test import TestCase

from apps.search.models import IpcAppList, AppDocuments, AppLimited, ObjType
from apps.search.services.application_data_writers import (ApplicationESWriter, ApplicationESTMWriter,
                                                           ApplicationESIDWriter, ApplicationESInvUMLDWriter,
                                                           ApplicationESMadridWriter, ApplicationESGeoWriter)
from apps.bulletin.models import EBulletinData


class ApplicationESWriterTestCase(TestCase):

    @mock.patch('apps.search.services.application_data_writers.datetime')
    @mock.patch("apps.search.services.application_data_writers.ApplicationESWriter._write_es")
    def test_update_db_data(self, mock_write_es, mock_datetime):
        now = datetime.datetime.now()
        mock_datetime.datetime.now.return_value = now

        app = IpcAppList.objects.create(
            last_indexation_date=None,
            elasticindexed=0,
            id_shedule_type=1
        )

        mock_write_es.return_value = False
        writer = ApplicationESWriter(app, {})
        writer.write()
        mock_write_es.assert_called()

        app.refresh_from_db()
        self.assertIsNone(app.last_indexation_date)
        self.assertFalse(app.elasticindexed)

        mock_write_es.return_value = True
        writer.write()
        mock_write_es.assert_called()
        app.refresh_from_db()
        self.assertEqual(app.last_indexation_date, now)
        self.assertTrue(app.elasticindexed)


class ApplicationESTMWriterTestCase(TestCase):

    @mock.patch("apps.search.services.application_data_writers.ApplicationESWriter._write_es")
    def test_write_441(self, mock_write_es):
        app = IpcAppList.objects.create(
            id_shedule_type=1
        )
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'Code_441': '2024-01-01',
                    'ApplicationNumber': 'm202400001',
                    'MarkImageDetails': {
                        'MarkImage': {}
                    }
                }
            }
        }

        mock_write_es.return_value = True
        writer = ApplicationESTMWriter(app, app_data)
        writer.write()

        bul_item = EBulletinData.objects.filter(app_number='m202400001').first()
        self.assertEqual(bul_item.publication_date.strftime('%Y-%m-%d'), '2024-01-01')
        self.assertEqual(bul_item.unit_id, 1)

        app_data['TradeMark']['TrademarkDetails']['Code_441'] = '2024-02-02'
        writer.write()
        self.assertEqual(EBulletinData.objects.filter(app_number='m202400001').count(), 1)
        bul_item = EBulletinData.objects.filter(app_number='m202400001').first()
        self.assertEqual(bul_item.publication_date.strftime('%Y-%m-%d'), '2024-02-02')
        self.assertEqual(bul_item.unit_id, 1)


class ApplicationESIDWriterTestCase(TestCase):

    @mock.patch("apps.search.services.application_data_writers.ApplicationESWriter._write_es")
    def test_delete_limited_images(self, mock_write_es):
        if os.path.exists('/tmp/s202400001/'):
            shutil.rmtree('/tmp/s202400001/')
        os.makedirs('/tmp/s202400001/')
        for i in range(5):
            file = open(f'/tmp/s202400001/{i}.jpg', 'w')
            file.close()

        app = IpcAppList(files_path='/tmp/s202400001/', id_shedule_type=1)
        app_data = {
            'Document': {
                'is_limited': False
            },
            'TradeMark': {
                'TrademarkDetails': {
                    'Code_441': '2024-01-01',
                    'ApplicationNumber': 'm202400001',
                    'MarkImageDetails': {
                        'MarkImage': {}
                    }
                }
            }
        }
        mock_write_es.return_value = True
        writer = ApplicationESIDWriter(app, app_data)
        writer.write()
        for i in range(5):
            self.assertTrue(os.path.exists(f'/tmp/s202400001/{i}.jpg'))

        app_data['Document']['is_limited'] = True
        writer.write()
        for i in range(5):
            self.assertFalse(os.path.exists(f'/tmp/s202400001/{i}.jpg'))


class ApplicationESInvUMLDWriterTestCase(TestCase):

    @mock.patch("apps.search.services.application_data_writers.ApplicationESWriter._write_es")
    def test_delete_limited_files(self, mock_write_es):
        app = IpcAppList.objects.create(files_path='/tmp/a202400001/', id_shedule_type=1)
        documents = [
            {'name': '/tmp/a202400001/AB.pdf', 'enter_num': 100, 'file_type': 'pdf'},
            {'name': '/tmp/a202400001/CL.pdf', 'enter_num': 98, 'file_type': 'pdf'},
            {'name': '/tmp/a202400001/a202400001.json', 'enter_num': 98, 'file_type': 'json'},
            {'name': '/tmp/a202400001/DE.pdf', 'enter_num': 99, 'file_type': 'pdf'},
            {'name': '/tmp/a202400001/DE2.pdf', 'enter_num': 101, 'file_type': 'pdf'},
        ]
        if os.path.exists('/tmp/a202400001/'):
            shutil.rmtree('/tmp/a202400001/')
        os.makedirs('/tmp/a202400001/')
        for doc in documents:
            file = open(doc['name'], 'w')
            file.close()
            AppDocuments.objects.create(
                app=app,
                file_type=doc['file_type'],
                file_name=doc['name'],
                enter_num=doc['enter_num'],
                add_date=datetime.datetime.now()
            )
        obj_type = ObjType.objects.create(obj_type_ua='Винаходи')
        app_data = {
            'Document': {
                'is_limited': False,
                'idObjType': obj_type.pk
            },
            'Patent': {
                'I_21': 'a202400001'
            }
        }

        mock_write_es.return_value = True
        writer = ApplicationESInvUMLDWriter(app, app_data)
        writer.write()

        for doc in documents:
            self.assertTrue(os.path.exists(doc['name']))

        # Тест если задано какие документы удалять
        app_limited = AppLimited.objects.create(
            app_number='a202400001',
            obj_type=obj_type,
            settings_json=json.dumps(
                {
                    'AB': False,
                    'DE': False,
                    'CL': False,
                }
            )
        )
        app_data['Document']['is_limited'] = True
        writer = ApplicationESInvUMLDWriter(app, app_data)
        writer.write()
        self.assertFalse(os.path.exists('/tmp/a202400001/AB.pdf'))
        self.assertFalse(os.path.exists('/tmp/a202400001/CL.pdf'))
        self.assertFalse(os.path.exists('/tmp/a202400001/DE.pdf'))
        self.assertFalse(os.path.exists('/tmp/a202400001/DE2.pdf'))
        self.assertTrue(os.path.exists('/tmp/a202400001/a202400001.json'))

        # Тест если не задано какие документы удалять (удаляются все)
        for doc in documents:
            file = open(doc['name'], 'w')
            file.close()
        app_limited.settings_json = '{}'
        app_limited.save()
        writer = ApplicationESInvUMLDWriter(app, app_data)
        writer.write()
        self.assertFalse(os.path.exists('/tmp/a202400001/AB.pdf'))
        self.assertFalse(os.path.exists('/tmp/a202400001/CL.pdf'))
        self.assertFalse(os.path.exists('/tmp/a202400001/DE.pdf'))
        self.assertFalse(os.path.exists('/tmp/a202400001/DE2.pdf'))
        self.assertTrue(os.path.exists('/tmp/a202400001/a202400001.json'))


class ApplicationESMadridWriterTestCase(TestCase):

    @mock.patch("apps.search.services.application_data_writers.ApplicationESMadridWriter._write_450")
    @mock.patch("apps.search.services.application_data_writers.ApplicationESWriter._write_es")
    def test_write_441(self, mock_write_es, mock_write_450):
        app = IpcAppList.objects.create(registration_number='12345', id_shedule_type=1)

        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    'Code_441': '2024-01-01'
                }
            }
        }

        mock_write_es.return_value = True
        writer = ApplicationESMadridWriter(app, app_data)
        writer.write()

        bul_item = EBulletinData.objects.filter(app_number='12345').first()
        self.assertEqual(bul_item.publication_date.strftime('%Y-%m-%d'), '2024-01-01')
        self.assertEqual(bul_item.unit_id, 2)

        app_data['MadridTradeMark']['TradeMarkDetails']['Code_441'] = '2024-02-02'
        writer.write()
        self.assertEqual(EBulletinData.objects.filter(app_number='12345').count(), 1)
        bul_item = EBulletinData.objects.filter(app_number='12345').first()
        self.assertEqual(bul_item.publication_date.strftime('%Y-%m-%d'), '2024-02-02')
        self.assertEqual(bul_item.unit_id, 2)


class ApplicationESGeoWriterTestCase(TestCase):

    @mock.patch("apps.search.services.application_data_writers.ApplicationESWriter._write_es")
    def test_write_441(self, mock_write_es):
        app = IpcAppList.objects.create(id_shedule_type=1)

        app_data = {
            'Geo': {
                'GeoDetails': {
                    'ApplicationNumber': 'i202400001',
                    'ApplicationPublicationDetails': {
                        'PublicationDate': '2024-01-01'
                    }
                }
            }
        }

        mock_write_es.return_value = True
        writer = ApplicationESGeoWriter(app, app_data)
        writer.write()

        bul_item = EBulletinData.objects.filter(app_number='i202400001').first()
        self.assertEqual(bul_item.publication_date.strftime('%Y-%m-%d'), '2024-01-01')
        self.assertEqual(bul_item.unit_id, 3)

        app_data['Geo']['GeoDetails']['ApplicationPublicationDetails']['PublicationDate'] = '2024-02-02'
        writer.write()
        self.assertEqual(EBulletinData.objects.filter(app_number='i202400001').count(), 1)
        bul_item = EBulletinData.objects.filter(app_number='i202400001').first()
        self.assertEqual(bul_item.publication_date.strftime('%Y-%m-%d'), '2024-02-02')
        self.assertEqual(bul_item.unit_id, 3)
