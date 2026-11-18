import json

from django.test import RequestFactory, TestCase

from apps.search.models import AppLimited, ObjType
from apps.search.services import MediaFileAccessService
from apps.search.services.doc_access import (
    IDMediaAccessChecker,
    InvUMLDMediaAccessChecker,
    TMMediaAccessChecker,
)
from apps.search.views import serve_protected_media


class MediaAccessCheckersTestCase(TestCase):
    """Тести класів перевірки доступу для окремих типів об'єктів."""

    def test_inv_um_ld_checker_abstract(self):
        checker = InvUMLDMediaAccessChecker()
        self.assertFalse(checker.has_access("100_abstract.pdf", {"AB": False}))
        self.assertFalse(checker.has_access("100_abstract.pdf", {}))
        self.assertTrue(checker.has_access("100_abstract.pdf", {"AB": True}))

    def test_inv_um_ld_checker_claims(self):
        checker = InvUMLDMediaAccessChecker()
        self.assertFalse(checker.has_access("98_claims.pdf", {"CL": False}))
        self.assertFalse(checker.has_access("98_claims.pdf", {}))
        self.assertTrue(checker.has_access("98_claims.pdf", {"CL": True}))

    def test_inv_um_ld_checker_description(self):
        checker = InvUMLDMediaAccessChecker()
        filenames = (
            "99_description.pdf",
            "101_pub_description.pdf",
            "published_description.pdf",
            "published_description_v2.pdf",
        )
        for filename in filenames:
            with self.subTest(filename=filename):
                self.assertFalse(checker.has_access(filename, {"DE": False}))
                self.assertFalse(checker.has_access(filename, {}))
                self.assertTrue(checker.has_access(filename, {"DE": True}))

    def test_inv_um_ld_checker_unrestricted_other_files(self):
        checker = InvUMLDMediaAccessChecker()
        self.assertTrue(checker.has_access("120_letter.pdf", {"AB": False, "DE": False, "CL": False}))
        self.assertTrue(checker.has_access("drawing.pdf", {}))

    def test_tm_checker(self):
        checker = TMMediaAccessChecker()
        self.assertFalse(checker.has_access("m202400001.jpg", {"MarkImageFilename": False}))
        self.assertFalse(checker.has_access("m202400001.jpg", {}))
        self.assertTrue(checker.has_access("m202400001.jpg", {"MarkImageFilename": True}))

    def test_id_checker(self):
        checker = IDMediaAccessChecker()
        self.assertFalse(checker.has_access("s202400001_1.jpg", {"DesignSpecimenDetails": False}))
        self.assertFalse(checker.has_access("s202400001_1.jpg", {}))
        self.assertTrue(checker.has_access("s202400001_1.jpg", {"DesignSpecimenDetails": True}))


class MediaFileAccessServiceTestCase(TestCase):
    """Тести сервісу MediaFileAccessService."""

    @classmethod
    def setUpTestData(cls):
        ObjType.objects.get_or_create(id=1, defaults={"obj_type_ua": "Винаходи", "obj_type_en": "Inventions"})
        ObjType.objects.get_or_create(id=2, defaults={"obj_type_ua": "Корисні моделі", "obj_type_en": "Utility models"})
        ObjType.objects.get_or_create(id=3, defaults={"obj_type_ua": "Компонування НМП", "obj_type_en": "Layout designs"})
        ObjType.objects.get_or_create(id=4, defaults={"obj_type_ua": "Торговельні марки", "obj_type_en": "Trade marks"})
        ObjType.objects.get_or_create(id=6, defaults={"obj_type_ua": "Промислові зразки", "obj_type_en": "Industrial designs"})

    def setUp(self):
        AppLimited.objects.all().delete()

    def test_unrestricted_application_has_access(self):
        paths = (
            "INVENTIONS/2021/a202102173/100_abstract.pdf",
            "UTILITY_MOD/2022/u202201111/99_desc.pdf",
            "TRADE_MARKS/2024/m202400001/image.jpg",
            "INDUSTRIAL_DES/2024/s202400001/specimen.jpg",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(MediaFileAccessService(path).has_access())

    def test_cancelled_limits_allow_access(self):
        AppLimited.objects.create(
            app_number="a202102173",
            obj_type_id=1,
            settings_json=json.dumps({"AB": False, "DE": False, "CL": False}),
            cancelled=True,
        )
        AppLimited.objects.create(
            app_number="m202400001",
            obj_type_id=4,
            settings_json=json.dumps({"MarkImageFilename": False}),
            cancelled=True,
        )
        AppLimited.objects.create(
            app_number="s202400001",
            obj_type_id=6,
            settings_json=json.dumps({"DesignSpecimenDetails": False}),
            cancelled=True,
        )

        self.assertTrue(MediaFileAccessService("INVENTIONS/2021/a202102173/100_abstract.pdf").has_access())
        self.assertTrue(MediaFileAccessService("TRADE_MARKS/2024/m202400001/mark.jpg").has_access())
        self.assertTrue(MediaFileAccessService("INDUSTRIAL_DES/2024/s202400001/specimen.jpg").has_access())

    def test_inventions_and_utility_models_restrictions(self):
        AppLimited.objects.create(
            app_number="a202102173",
            obj_type_id=1,
            settings_json=json.dumps({"AB": False, "DE": True, "CL": False}),
            cancelled=False,
        )

        self.assertFalse(MediaFileAccessService("INVENTIONS/2021/a202102173/100_abstract.pdf").has_access())
        self.assertFalse(MediaFileAccessService("INVENTIONS/2021/a202102173/98_claims.pdf").has_access())
        self.assertTrue(MediaFileAccessService("INVENTIONS/2021/a202102173/99_description.pdf").has_access())
        self.assertTrue(MediaFileAccessService("INVENTIONS/2021/a202102173/published_description.pdf").has_access())

    def test_trademark_image_restrictions(self):
        app_limited = AppLimited.objects.create(
            app_number="m202400001",
            obj_type_id=4,
            settings_json=json.dumps({"MarkImageFilename": False}),
            cancelled=False,
        )
        self.assertFalse(MediaFileAccessService("TRADE_MARKS/2024/m202400001/m202400001.jpg").has_access())

        app_limited.settings_json = json.dumps({"MarkImageFilename": True})
        app_limited.save()
        self.assertTrue(MediaFileAccessService("TRADE_MARKS/2024/m202400001/m202400001.jpg").has_access())

    def test_industrial_design_image_restrictions(self):
        app_limited = AppLimited.objects.create(
            app_number="s202400001",
            obj_type_id=6,
            settings_json=json.dumps({"DesignSpecimenDetails": False}),
            cancelled=False,
        )
        self.assertFalse(MediaFileAccessService("INDUSTRIAL_DES/2024/s202400001/specimen_1.jpg").has_access())

        app_limited.settings_json = json.dumps({"DesignSpecimenDetails": True})
        app_limited.save()
        self.assertTrue(MediaFileAccessService("INDUSTRIAL_DES/2024/s202400001/specimen_1.jpg").has_access())

    def test_obj_type_isolation_for_same_app_number(self):
        """Якщо однаковий цифровий app_number існує для різних типів ОПВ, перевіряється саме свій obj_type_id."""
        AppLimited.objects.create(
            app_number="2003010035",
            obj_type_id=1,
            settings_json=json.dumps({"AB": False}),
            cancelled=False,
        )
        # Для промислового зразка (id=6) з тим самим номером обмежень немає
        self.assertTrue(MediaFileAccessService("INDUSTRIAL_DES/2003/2003010035/img.jpg").has_access())
        # Для винаходу (id=1) обмеження діє
        self.assertFalse(MediaFileAccessService("INVENTIONS/2003/2003010035/100_ab.pdf").has_access())

    def test_case_insensitivity_and_nested_subdirectories(self):
        AppLimited.objects.create(
            app_number="a202102173",
            obj_type_id=1,
            settings_json=json.dumps({"AB": False}),
            cancelled=False,
        )
        self.assertFalse(MediaFileAccessService("inventions/2021/a202102173/100_abstract.pdf").has_access())
        self.assertFalse(MediaFileAccessService("INVENTIONS/2021/a202102173/nested/100_abstract.pdf").has_access())

    def test_unmatched_path_returns_true(self):
        self.assertTrue(MediaFileAccessService("OTHER_FOLDER/file.pdf").has_access())


class ServeProtectedMediaViewTestCase(TestCase):
    """Тести контролера serve_protected_media."""

    @classmethod
    def setUpTestData(cls):
        ObjType.objects.get_or_create(id=1, defaults={"obj_type_ua": "Винаходи", "obj_type_en": "Inventions"})
        ObjType.objects.get_or_create(id=4, defaults={"obj_type_ua": "Торговельні марки", "obj_type_en": "Trade marks"})

    def setUp(self):
        self.factory = RequestFactory()
        AppLimited.objects.all().delete()

    def test_forbidden_when_access_denied(self):
        AppLimited.objects.create(
            app_number="a202102173",
            obj_type_id=1,
            settings_json=json.dumps({"AB": False}),
            cancelled=False,
        )
        request = self.factory.get("/media/INVENTIONS/2021/a202102173/100_abstract.pdf")
        response = serve_protected_media(request, "INVENTIONS/2021/a202102173/100_abstract.pdf")
        self.assertEqual(response.status_code, 403)

    def test_x_accel_redirect_for_allowed_pdf(self):
        file_path = "INVENTIONS/2021/a202102173/100_реферат з пробілами.pdf"
        request = self.factory.get(f"/media/{file_path}")
        response = serve_protected_media(request, file_path)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["X-Accel-Redirect"],
            "/INVENTIONS/2021/a202102173/100_%D1%80%D0%B5%D1%84%D0%B5%D1%80%D0%B0%D1%82%20%D0%B7%20%D0%BF%D1%80%D0%BE%D0%B1%D1%96%D0%BB%D0%B0%D0%BC%D0%B8.pdf",
        )
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_x_accel_redirect_for_allowed_image(self):
        file_path = "TRADE_MARKS/2024/m202400001/mark.jpg"
        request = self.factory.get(f"/media/{file_path}")
        response = serve_protected_media(request, file_path)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Accel-Redirect"], "/TRADE_MARKS/2024/m202400001/mark.jpg")
        self.assertEqual(response["Content-Type"], "image/jpeg")

