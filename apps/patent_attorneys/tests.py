from django.test import TestCase
from django.urls import reverse

from apps.patent_attorneys.models import PatentAttorneyExt


class PatentAttorneyListViewTestCase(TestCase):

    def test_no_records(self):
        response = self.client.get(reverse('patent_attorneys:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Патентні повірені відсутні.')
        self.assertQuerysetEqual(response.context['object_list'], [])

    def test_table_contains_records(self):
        PatentAttorneyExt.objects.create(
            prizv='Test_prizv',
            name='Test_name',
            po_batk='Test_po_batk',
        )
        response = self.client.get(reverse('patent_attorneys:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test_prizv')
        self.assertContains(response, 'Test_name')
        self.assertContains(response, 'Test_po_batk')

    def test_pagination(self):
        PatentAttorneyExt.objects.all().delete()
        for i in range(101):
            PatentAttorneyExt.objects.create(
                prizv=f'Test_prizv_{i}',
                name=f'Test_name_{i}',
                po_batk=f'Test_po_batk_{i}',
            )
        for n in (10, 20, 50, 100):  # Позволенные значения количества строк в таблице
            response = self.client.get(f"{reverse('patent_attorneys:list')}?show={n}")
            self.assertEqual(response.status_code, 200)
            for i in range(n):
                self.assertContains(response, f'Test_prizv_{i}')
                self.assertContains(response, f'Test_name_{i}')
                self.assertContains(response, f'Test_po_batk_{i}')
            self.assertNotContains(response, f'Test_po_batk_{n+1}')

            response = self.client.get(f"{reverse('patent_attorneys:list')}?show={n+1}")
            self.assertEqual(response.status_code, 404)

    def test_table_filtering(self):
        PatentAttorneyExt.objects.all().delete()
        for i in range(100):
            PatentAttorneyExt.objects.create(
                reg_num=i,
                prizv=f'Test_prizv_{i}',
                name=f'Test_name_{i}',
                po_batk=f'Test_po_batk_{i}',
                special=f'special_{i}',
                postaladdress=f'postaladdress_{i}',
                phones=f'phones_{i}',
                e_mail=f'e_mail_{i}',
            )
        response = self.client.get(f"{reverse('patent_attorneys:list')}?reg_num=90")
        self.assertContains(response, 'Test_prizv_90')
        self.assertContains(response, 'Test_name_90')
        self.assertContains(response, 'Test_po_batk_90')

        response = self.client.get(f"{reverse('patent_attorneys:list')}?name=prizv_45")
        self.assertContains(response, 'Test_prizv_45')
        self.assertContains(response, 'Test_name_45')
        self.assertContains(response, 'Test_po_batk_45')

        response = self.client.get(f"{reverse('patent_attorneys:list')}?special=special_45")
        self.assertContains(response, 'special_45')

        response = self.client.get(f"{reverse('patent_attorneys:list')}?postal_address=address_60")
        self.assertContains(response, 'postaladdress_60')
        response = self.client.get(f"{reverse('patent_attorneys:list')}?postal_address=phones_60")
        self.assertContains(response, 'phones_60')
        response = self.client.get(f"{reverse('patent_attorneys:list')}?postal_address=e_mail_60")
        self.assertContains(response, 'e_mail_60')

    def test_table_sorting(self):
        PatentAttorneyExt.objects.all().delete()
        for i in range(1, 10):
            PatentAttorneyExt.objects.create(
                reg_num=i,
                prizv=f'Test_prizv_{i}',
                name=f'Test_name_{i}',
                po_batk=f'Test_po_batk_{i}',
                special=f'special_{i}',
                postaladdress=f'postaladdress_{i}',
                phones=f'phones_{i}',
                e_mail=f'e_mail_{i}',
                dat_reg=f'2024-01-0{i}'
            )
        response = self.client.get(f"{reverse('patent_attorneys:list')}?sort_by=regnum_asc")
        content = str(response.content)
        self.assertTrue(content.index('<td>1</td>') < content.index('<td>2</td>'))
        response = self.client.get(f"{reverse('patent_attorneys:list')}?sort_by=regnum_desc")
        content = str(response.content)
        self.assertTrue(content.index('<td>2</td>') < content.index('<td>1</td>'))

        response = self.client.get(f"{reverse('patent_attorneys:list')}?sort_by=regnum_asc")
        content = str(response.content)
        self.assertTrue(content.index('01.01.2024') < content.index('02.01.2024'))
        response = self.client.get(f"{reverse('patent_attorneys:list')}?sort_by=regnum_desc")
        content = str(response.content)
        self.assertTrue(content.index('02.01.2024') < content.index('01.01.2024'))

        response = self.client.get(f"{reverse('patent_attorneys:list')}?sort_by=name_asc")
        content = str(response.content)
        self.assertTrue(content.index('Test_prizv_1') < content.index('Test_prizv_2'))
        response = self.client.get(f"{reverse('patent_attorneys:list')}?sort_by=name_desc")
        content = str(response.content)
        self.assertTrue(content.index('Test_prizv_2') < content.index('Test_prizv_1'))
