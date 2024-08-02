from django.test import TestCase

from apps.search.services.application_indexators import ApplicationIndexationService
from apps.search.models import IpcAppList, ObjType


class ApplicationIndexationServiceTestCase(TestCase):
    """Тестирует класс ApplicationIndexationService."""
    def test_get_apps_for_indexation(self):
        """Тестирует метод get_apps_for_indexation."""
        obj_type_inv = ObjType.objects.create(obj_type_ua='Винаходи')
        obj_type_tm = ObjType.objects.create(obj_type_ua='Торговельні марки')
        app_1 = IpcAppList.objects.create(app_number='a200400001', obj_type=obj_type_inv, elasticindexed=0,
                                          id_shedule_type=1)
        app_2 = IpcAppList.objects.create(app_number='a200400002', obj_type=obj_type_inv, elasticindexed=1,
                                          id_shedule_type=1)
        app_3 = IpcAppList.objects.create(app_number='m200400001', obj_type=obj_type_tm, elasticindexed=0,
                                          id_shedule_type=1)
        app_4 = IpcAppList.objects.create(app_number='m200400002', registration_number='111111',
                                          registration_date='2024-07-08', obj_type=obj_type_tm,
                                          elasticindexed=1, id_shedule_type=1)

        apps = ApplicationIndexationService.get_apps_for_indexation()
        self.assertEqual(apps.count(), 2)
        for app in apps:
            self.assertEqual(app.elasticindexed, 0)

        apps = ApplicationIndexationService.get_apps_for_indexation(ignore_indexed=True)
        self.assertEqual(apps.count(), 4)

        apps = ApplicationIndexationService.get_apps_for_indexation(app_id=app_1.pk)
        self.assertEqual(apps.count(), 1)
        self.assertEqual(apps[0].pk, app_1.pk)

        apps = ApplicationIndexationService.get_apps_for_indexation(obj_type=obj_type_inv.pk, ignore_indexed=True)
        self.assertEqual(apps.count(), 2)
        for app in apps:
            self.assertEqual(app.obj_type_id, obj_type_inv.pk)

        apps = ApplicationIndexationService.get_apps_for_indexation(status=1, ignore_indexed=True)
        self.assertEqual(apps.count(), 3)
        for app in apps:
            self.assertIsNone(app.registration_number)
        apps = ApplicationIndexationService.get_apps_for_indexation(status=2, ignore_indexed=True)
        self.assertEqual(apps.count(), 1)
        for app in apps:
            self.assertIsNotNone(app.registration_number)
