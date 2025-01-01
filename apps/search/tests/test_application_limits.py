from django.test import TestCase

from apps.search.models import AppLimited, ObjType
from apps.search.services.application_limits import (
    LimitsMucToDictConverterInvUMLD,
    LimitsMucToDictConverterID,
    LimitsMucToDictConverterCR,
    LimitsMucToDictConverterDecision,
    LimitsService,
    LIMITS_STATUS,
)


class LimitsMucToJSONConverterTests(TestCase):

    def test_limits_muc_to_json_converter_inv_umld(self):
        """Тест конвертора для винаходів, КМ, топографій (LimitsMucToJSONConverterInvUMLD)."""
        muc_limits = {1, 3, 5}
        converter = LimitsMucToDictConverterInvUMLD(muc_limits)
        result = converter.convert()

        expected = {
            'I_71': False,
            'I_72': True,
            'I_73': False,
            'I_98': True,
            'I_98_Index': True,
            'CL': False,
            'DE': True,
            'AB': True,
            'I_54': True,
            'I_56': True,
            'I_74': True,
        }

        self.assertEqual(result, expected)

    def test_limits_muc_to_json_converter_id(self):
        """Тест конвертора для промислових зразків (LimitsMucToJSONConverterID)."""
        muc_limits = {40, 42, 45}
        converter = LimitsMucToDictConverterID(muc_limits)
        result = converter.convert()

        expected = {
            'DesignSpecimenDetails': False,
            'ApplicantDetails': True,
            'DesignerDetails': False,
            'HolderDetails': True,
            'CorrespondenceAddress': True,
            'DesignTitle': False,
            'RepresentativeDetails': True,
        }

        self.assertEqual(result, expected)

    def test_limits_muc_to_json_converter_cr(self):
        """Тест конвертора для авторського права (LimitsMucToJSONConverterCR)."""
        muc_limits = {12, 14, 17}
        converter = LimitsMucToDictConverterCR(muc_limits)
        result = converter.convert()

        expected = {
            'AuthorDetails': False,
            'ApplicantDetails': False,
            'PromulgationData': True,
            'Annotation': False,
            'HolderDetails': True,
            'EmployerDetails': True,
            'RepresentativeDetails': True,
            'Name': False,
            'NameShort': False,
        }

        self.assertEqual(result, expected)

    def test_limits_muc_to_json_converter_decision(self):
        """Тест конвертора для договорів авторського права (LimitsMucToJSONConverterDecision)."""
        muc_limits = {18, 37, 39}
        converter = LimitsMucToDictConverterDecision(muc_limits)
        result = converter.convert()

        expected = {
            'LicenseeDetails': False,
            'LicensorDetails': False,
            'RegistrationKind': True,
            'RegistrationKindCode': True,
            'AuthorDetails': True,
            'ApplicantDetails': True,
            'Annotation': False,
            'Name': True,
            'NameShort': True,
            'RepresentativeDetails': False,
        }

        self.assertEqual(result, expected)

    def test_limits_muc_to_json_converter_empty_limits(self):
        """Тест усіх конверторів с пустим набором обмежень."""
        converters = [
            LimitsMucToDictConverterInvUMLD(),
            LimitsMucToDictConverterID(),
            LimitsMucToDictConverterCR(),
            LimitsMucToDictConverterDecision(),
        ]

        for converter in converters:
            with self.subTest(converter=converter.__class__.__name__):
                result = converter.convert()

                # Все значения должны быть True, так как ограничений нет
                for key, value in result.items():
                    self.assertTrue(value)


class LimitsServiceTests(TestCase):

    def setUp(self):
        self.obj_type = ObjType.objects.create(obj_type_ua='Винаходи')

        AppLimited.objects.create(
            app_number="12345",
            obj_type_id=self.obj_type.pk,
            settings_json='{\n    "I_71": true\n}',
            cancelled=False
        )

    def test_process_create_record(self):
        """Тест створення нового запису якщо він відсутній."""
        service = LimitsService(
            app_number="67890",
            obj_type_id=self.obj_type.pk,
            limits_status=LIMITS_STATUS['SET'],
            limits={"I_71": False}
        )

        result = service.process()
        self.assertTrue(result)

        # Проверяем, что запись создалась
        record = AppLimited.objects.filter(app_number="67890", obj_type_id=self.obj_type.pk).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.settings_json, '{\n    "I_71": false\n}')
        self.assertFalse(record.cancelled)

    def test_process_update_record(self):
        """Тест оновлення існуючого запису."""
        service = LimitsService(
            app_number="12345",
            obj_type_id=1,
            limits_status=LIMITS_STATUS['SET'],
            limits={"I_71": False}
        )

        result = service.process()
        self.assertTrue(result)

        # Проверяем, что запись обновилась
        record = AppLimited.objects.get(app_number="12345", obj_type_id=self.obj_type.pk)
        self.assertEqual(record.settings_json, '{\n    "I_71": false\n}')
        self.assertFalse(record.cancelled)

    def test_process_no_limits(self):
        """Тест: удаление записи при отсутствии ограничений."""
        service = LimitsService(
            app_number="12345",
            obj_type_id=1,
            limits_status=LIMITS_STATUS['NONE'],
            limits={}
        )

        result = service.process()
        self.assertTrue(result)

        # Проверяем, что запись удалена
        record = AppLimited.objects.filter(app_number="12345", obj_type_id=self.obj_type.pk).first()
        self.assertIsNone(record)

    def test_process_no_changes(self):
        """Тест: отсутствие изменений, если данные совпадают."""
        service = LimitsService(
            app_number="12345",
            obj_type_id=self.obj_type.pk,
            limits_status=LIMITS_STATUS['SET'],
            limits={"I_71": True}
        )

        result = service.process()
        self.assertFalse(result)

        # Проверяем, что запись не изменилась
        record = AppLimited.objects.get(app_number="12345", obj_type_id=self.obj_type.pk)
        self.assertEqual(record.settings_json, '{\n    "I_71": true\n}')
        self.assertFalse(record.cancelled)
