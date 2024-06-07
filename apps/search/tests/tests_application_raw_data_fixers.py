from django.test import TestCase
from apps.search.services.application_raw_data_fixers import ApplicationTMRawDataFixerFS


class TestApplicationTMRawDataFixerFSTestCase(TestCase):
    """Тестирует класс ApplicationTMRawDataFixerFS"""

    def test_fix_files_path(self):
        app_data = {
            'Document': {
                'filesPath': 'e:\\poznach_test_sis\\bear_tmpp_sis\\TRADE_MARKS\\2024\\m202400001'
            }
        }
        ApplicationTMRawDataFixerFS.fix_files_path(app_data)
        self.assertEqual(app_data['Document']['filesPath'], '\\\\bear\\share\\TRADE_MARKS\\2024\\m202400001\\')

    def test_fix_sections(self):
        app_data = {
            'TradeMark': {},
            'PaymentDetails': {},
            'DocFlow': {},
            'Transactions': {},
        }
        ApplicationTMRawDataFixerFS.fix_sections(app_data)
        self.assertIn('PaymentDetails', app_data['TradeMark'])
        self.assertIn('DocFlow', app_data['TradeMark'])
        self.assertIn('Transactions', app_data['TradeMark'])
        self.assertNotIn('PaymentDetails', app_data)
        self.assertNotIn('DocFlow', app_data)
        self.assertNotIn('Transactions', app_data)

    def test_fix_publication_date(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'PublicationDetails': {
                        'Publication': {
                            'PublicationDate': '03.06.2024',
                            'PublicationIdentifier': '14'
                        }
                    }
                }
            }
        }
        ApplicationTMRawDataFixerFS.fix_publication(app_data)
        self.assertIsInstance(app_data['TradeMark']['TrademarkDetails']['PublicationDetails'], list)
        self.assertEqual(
            app_data['TradeMark']['TrademarkDetails']['PublicationDetails'][0]['PublicationDate'],
            '2024-06-03'
        )
        self.assertEqual(
            app_data['TradeMark']['TrademarkDetails']['PublicationDetails'][0]['PublicationIdentifier'],
            '14/2024'
        )

    def test_fix_holder_original(self):
        self.fail('Finish the test')

    def test_fix_applicant_original(self):
        self.fail('Finish the test')

    def test_fix_associated_registration_details(self):
        self.fail('Finish the test')

    def test_fix_termination_date(self):
        self.fail('Finish the test')

    def test_fix_exhibition_termination_date(self):
        self.fail('Finish the test')

    def test_fix_transactions(self):
        self.fail('Finish the test')

    def test_fix_id_doc_cead(self):
        self.fail('Finish the test')
