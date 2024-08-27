from unittest import mock

from django.test import TestCase
from apps.search.services.application_raw_data_fixers import ApplicationRawDataFSTMFixer, ApplicationRawDataFSIDFixer, \
    ApplicationRawDataFSMadridFixer, ApplicationRawDataFSGeoFixer, ApplicationRawDataFSCRFixer


class TestApplicationTMRawDataFixerFSTestCase(TestCase):
    """Тестирует класс ApplicationTMRawDataFixerFS"""

    def setUp(self) -> None:
        self.fixer = ApplicationRawDataFSTMFixer()

    def test_fix_files_path(self):
        app_data = {
            'TradeMark': {},
            'Document': {
                'filesPath': 'e:\\poznach_test_sis\\bear_tmpp_sis\\TRADE_MARKS\\2024\\m202400001'
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['Document']['filesPath'], '\\\\bear\\share\\TRADE_MARKS\\2024\\m202400001\\')

    def test_fix_sections(self):
        app_data = {
            'TradeMark': {},
            'PaymentDetails': {},
            'DocFlow': {},
            'Transactions': {},
        }
        self.fixer.fix_data(app_data)
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
        self.fixer.fix_data(app_data)
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
        """Тестирует метод _fix_holder_original (исправление оригинальных наименований владельца)."""
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "HolderDetails": {
                        "Holder": [
                            {
                                "HolderAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": 'US',
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLineOriginal": "Test Data 1",
                                                "FreeFormatNameLineOriginal": "Test Data 2",
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLineOriginal": "Test Data 3"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        holder_name_address_data = app_data['TradeMark']['TrademarkDetails']['HolderDetails']['Holder'][0][
            'HolderAddressBook']['FormattedNameAddress']
        self.fixer.fix_data(app_data)
        self.assertEqual(
            "Test Data 1",
            holder_name_address_data['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal']
        )
        self.assertEqual(
            "Test Data 2",
            holder_name_address_data['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal']
        )
        self.assertEqual(
            "Test Data 3",
            holder_name_address_data['Name']['FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLineOriginal']
        )

        # Если владелец из Украины, то наименование языком оригинала быть в данных не должно
        holder_name_address_data['Address']['AddressCountryCode'] = 'UA'
        self.fixer.fix_data(app_data)
        self.assertNotIn(
            'FreeFormatAddressLineOriginal',
            holder_name_address_data['Address']['FreeFormatAddress']
        )
        self.assertNotIn(
            'FreeFormatNameLineOriginal',
            holder_name_address_data['Address']['FreeFormatAddress']
        )
        self.assertNotIn(
            'FreeFormatNameLineOriginal',
            holder_name_address_data['Name']['FreeFormatName']['FreeFormatNameDetails']
        )

        # Пустые значения также должны удаляться
        holder_name_address_data['Address']['AddressCountryCode'] = 'UK'
        holder_name_address_data['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal'] = ''
        holder_name_address_data['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal'] = ''
        holder_name_address_data['Name']['FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLineOriginal'] = ''
        self.fixer.fix_data(app_data)
        self.assertNotIn(
            'FreeFormatAddressLineOriginal',
            holder_name_address_data['Address']['FreeFormatAddress']
        )
        self.assertNotIn(
            'FreeFormatNameLineOriginal',
            holder_name_address_data['Address']['FreeFormatAddress']
        )
        self.assertNotIn(
            'FreeFormatNameLineOriginal',
            holder_name_address_data['Name']['FreeFormatName']['FreeFormatNameDetails']
        )

    def test_fix_applicant_original(self):
        """Тестирует метод _fix_holder_original (исправление оригинальных наименований владельца)."""
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ApplicantDetails": {
                        "Applicant": [
                            {
                                "ApplicantAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": "UK",
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLineOriginal": "Test Data 1",
                                                "FreeFormatNameLineOriginal": "Test Data 2"
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLineOriginal": "Test Data 3"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        applicant_name_address_data = app_data['TradeMark']['TrademarkDetails']['ApplicantDetails']['Applicant'][0][
            'ApplicantAddressBook']['FormattedNameAddress']
        self.fixer.fix_data(app_data)
        self.assertEqual(
            "Test Data 1",
            applicant_name_address_data['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal']
        )
        self.assertEqual(
            "Test Data 2",
            applicant_name_address_data['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal']
        )
        self.assertEqual(
            "Test Data 3",
            applicant_name_address_data['Name']['FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLineOriginal']
        )

        # Если владелец из Украины, то наименование языком оригинала быть в данных не должно
        applicant_name_address_data['Address']['AddressCountryCode'] = 'UA'
        self.fixer.fix_data(app_data)
        self.assertNotIn(
            'FreeFormatAddressLineOriginal',
            applicant_name_address_data['Address']['FreeFormatAddress']
        )
        self.assertNotIn(
            'FreeFormatNameLineOriginal',
            applicant_name_address_data['Address']['FreeFormatAddress']
        )
        self.assertNotIn(
            'FreeFormatNameLineOriginal',
            applicant_name_address_data['Name']['FreeFormatName']['FreeFormatNameDetails']
        )

        # Пустые значения также должны удаляться
        applicant_name_address_data['Address']['AddressCountryCode'] = 'UK'
        applicant_name_address_data['Address']['FreeFormatAddress']['FreeFormatAddressLineOriginal'] = ''
        applicant_name_address_data['Address']['FreeFormatAddress']['FreeFormatNameLineOriginal'] = ''
        applicant_name_address_data['Name']['FreeFormatName']['FreeFormatNameDetails'][
            'FreeFormatNameLineOriginal'] = ''
        self.fixer.fix_data(app_data)
        self.assertNotIn(
            'FreeFormatAddressLineOriginal',
            applicant_name_address_data['Address']['FreeFormatAddress']
        )
        self.assertNotIn(
            'FreeFormatNameLineOriginal',
            applicant_name_address_data['Address']['FreeFormatAddress']
        )
        self.assertNotIn(
            'FreeFormatNameLineOriginal',
            applicant_name_address_data['Name']['FreeFormatName']['FreeFormatNameDetails']
        )

    def test_fix_stages(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationNumber': '11111',
                    'stages': [
                        {
                            'title': 'stage_1',
                            'status': 'done'
                        },
                        {
                            'title': 'stage_2',
                            'status': 'active'
                        }
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['TradeMark']['TrademarkDetails']['stages'][0]['title'], 'stage_2')
        self.assertEqual(app_data['TradeMark']['TrademarkDetails']['stages'][0]['status'], 'done')
        self.assertEqual(app_data['TradeMark']['TrademarkDetails']['stages'][1]['title'], 'stage_1')
        self.assertEqual(app_data['TradeMark']['TrademarkDetails']['stages'][1]['status'], 'done')

    def test_fix_associated_registration_details(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'AssociatedRegistrationApplicationDetails': {
                        'AssociatedRegistrationApplication': {
                            'AssociatedRegistrationDetails': {
                                'DivisionalApplication': [
                                    {
                                        'AssociatedRegistration': {
                                            'AssociatedRegistrationDate': '11.07.2024',
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['TradeMark']['TrademarkDetails']['AssociatedRegistrationApplicationDetails'][
                             'AssociatedRegistrationApplication']['AssociatedRegistrationDetails'][
                             'DivisionalApplication'][0]['AssociatedRegistration'][
                             'AssociatedRegistrationDate'], '2024-07-11')

    def test_fix_termination_date(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'TerminationDate': '11.07.2024'
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['TradeMark']['TrademarkDetails']['TerminationDate'], '2024-07-11')

    def test_fix_exhibition_termination_date(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'ExhibitionPriorityDetails': [
                        {
                            'ExhibitionCountryCode': 'UA',
                            'ExhibitionDate': '2004-06-15',
                        }
                    ]
                }
            }
        }

        self.fixer.fix_data(app_data)
        self.assertIn('ExhibitionPriority', app_data['TradeMark']['TrademarkDetails']['ExhibitionPriorityDetails'])
        self.assertEqual(app_data['TradeMark']['TrademarkDetails']['ExhibitionPriorityDetails'][
                             'ExhibitionPriority'][0]['ExhibitionCountryCode'], 'UA')

    def test_fix_transactions(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationNumber': '111111'
                },
                'Transactions': {
                    'Transaction': [
                        {
                            '@registrationNumber': '22222'
                        },
                        {
                            '@registrationNumber': '111111',
                            'TransactionBody': {
                                'PublicationDate': '11.07.2024',
                                'PublicationNumber': '1',
                            }
                        },
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        for transaction in app_data['TradeMark']['Transactions']['Transaction']:
            # Нет "чужих" оповещений
            self.assertEqual(transaction['@registrationNumber'], '111111')

            self.assertEqual(
                transaction['TransactionBody']['PublicationDetails']['Publication']['PublicationDate'],
                '2024-07-11'
            )
            self.assertEqual(
                transaction['TransactionBody']['PublicationDetails']['Publication']['PublicationNumber'],
                '1'
            )

    @mock.patch("apps.search.services.application_raw_data_fixers.cead_get_id_doc")
    def test_fix_id_doc_cead(self, cead_get_id_doc):
        cead_get_id_doc.return_value = 111
        app_data = {
            'TradeMark': {
                "DocFlow": {
                    'Documents': [
                        {
                            'DocRecord': {
                                'DocBarCode': '12345',
                            }
                        },
                        {
                            'DocRecord': {
                                'DocBarCode': '67890',
                            }
                        }
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        for doc in app_data['TradeMark']['DocFlow']['Documents']:
            self.assertEqual(doc['DocRecord']['DocIdDocCEAD'], 111)


class TestApplicationIDRawDataFixerFSTestCase(TestCase):
    def setUp(self) -> None:
        self.fixer = ApplicationRawDataFSIDFixer()

    def test_fix_files_path(self):
        app_data = {
            'Design': {},
            'Document': {
                'filesPath': '\\\\bear\\share\\INDUSTRIAL_DES\\2024\\s202400001'
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['Document']['filesPath'], '\\\\bear\\share\\INDUSTRIAL_DES\\2024\\s202400001\\')

    def test_fix_indication_details(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    "IndicationProductDetails": [
                        {
                            "Class": "11.1",
                        }
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(
            app_data['Design']['DesignDetails']['IndicationProductDetails'][0]['Class'], '11-01'
        )

    def test_fix_sections(self):
        app_data = {
            'Design': {},
            'PaymentDetails': {},
            'DocFlow': {},
            'Transactions': {},
        }
        self.fixer.fix_data(app_data)
        self.assertIn('PaymentDetails', app_data['Design'])
        self.assertIn('DocFlow', app_data['Design'])
        self.assertIn('Transactions', app_data['Design'])
        self.assertNotIn('PaymentDetails', app_data)
        self.assertNotIn('DocFlow', app_data)
        self.assertNotIn('Transactions', app_data)

    def test_fix_publication_details(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    "RecordPublicationDetails": [
                        {
                            "PublicationDate": "2024-01-01",
                            "PublicationIdentifier": "1"
                        }
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(
            app_data['Design']['DesignDetails']['RecordPublicationDetails'][0]['PublicationIdentifier'], '1/2024'
        )

        app_data = {
            'Design': {
                'DesignDetails': {
                    "RecordPublicationDetails": [
                        {
                            "PublicationDate": "2024-01-01",
                            "PublicationIdentifier": "1/2024"
                        }
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(
            app_data['Design']['DesignDetails']['RecordPublicationDetails'][0]['PublicationIdentifier'], '1/2024'
        )

    def test_fix_stages(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'RegistrationNumber': '11111',
                    'stages': [
                        {
                            'title': 'stage_1',
                            'status': 'done'
                        },
                        {
                            'title': 'stage_2',
                            'status': 'active'
                        }
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['Design']['DesignDetails']['stages'][0]['title'], 'stage_2')
        self.assertEqual(app_data['Design']['DesignDetails']['stages'][0]['status'], 'done')
        self.assertEqual(app_data['Design']['DesignDetails']['stages'][1]['title'], 'stage_1')
        self.assertEqual(app_data['Design']['DesignDetails']['stages'][1]['status'], 'done')

    def test_fix_priority_date(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'PriorityDetails': {
                        'Priority': [
                            {
                                'PriorityDate': '2024-01-01'
                            },
                            {
                                'PriorityDate': ''
                            }
                        ]
                    }
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertIn('PriorityDate', app_data['Design']['DesignDetails']['PriorityDetails']['Priority'][0])
        self.assertNotIn('PriorityDate', app_data['Design']['DesignDetails']['PriorityDetails']['Priority'][1])

    def test_fix_transactions(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'RegistrationNumber': '111111'
                },
                'Transactions': {
                    'Transaction': [
                        {
                            '@registrationNumber': '22222'
                        },
                        {
                            '@registrationNumber': '111111',
                            'TransactionBody': {
                                'PublicationDetails': {
                                    'Publication': {
                                        'PublicationDate': '11.07.2024',
                                        'PublicationNumber': '1',
                                    }
                                },
                                'DesignerDetails': {
                                    'Designer': [
                                        {'DesignerAddressBook': {}}
                                    ]
                                }
                            }
                        },
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        for transaction in app_data['Design']['Transactions']['Transaction']:
            # Нет "чужих" оповещений
            self.assertEqual(transaction['@registrationNumber'], '111111')

            self.assertEqual(
                transaction['TransactionBody']['PublicationDetails']['Publication']['PublicationDate'],
                '2024-07-11'
            )
            self.assertEqual(
                transaction['TransactionBody']['PublicationDetails']['Publication']['PublicationNumber'],
                '1'
            )

            # DesignerDetails.Designer у сповіщеннях має бути словником
            self.assertIsInstance(transaction['TransactionBody']['DesignerDetails']['Designer'], dict)

        # Існують випадки коли у сповіщенні "DesignerDetails": None, корекція даних має проходити
        app_data = {
            'Design': {
                'DesignDetails': {
                    'RegistrationNumber': '111111'
                },
                'Transactions': {
                    'Transaction': [
                        {
                            '@registrationNumber': '111111',
                            'TransactionBody': {
                                'DesignerDetails': None,
                            }
                        },
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)

    @mock.patch("apps.search.services.application_raw_data_fixers.cead_get_id_doc")
    def test_fix_id_doc_cead(self, cead_get_id_doc):
        cead_get_id_doc.return_value = 111
        app_data = {
            'Design': {
                "DocFlow": {
                    'Documents': [
                        {
                            'DocRecord': {
                                'DocBarCode': '12345',
                            }
                        },
                        {
                            'DocRecord': {
                                'DocBarCode': '67890',
                            }
                        }
                    ]
                }
            }
        }
        self.fixer.fix_data(app_data)
        for doc in app_data['Design']['DocFlow']['Documents']:
            self.assertEqual(doc['DocRecord']['DocIdDocCEAD'], 111)


class ApplicationRawDataFSMadridFixerTestCase(TestCase):
    def setUp(self) -> None:
        self.fixer = ApplicationRawDataFSMadridFixer()

    def test_fix_dates(self):
        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    '@EXPDATE': '20240101',
                    '@NOTDATE': '20240102',
                    '@REGEDAT': '20240103',
                    '@REGRDAT': '20240104',
                    '@INTREGD': '20240105',
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['MadridTradeMark']['TradeMarkDetails']['@EXPDATE'], '2024-01-01')
        self.assertEqual(app_data['MadridTradeMark']['TradeMarkDetails']['@NOTDATE'], '2024-01-02')
        self.assertEqual(app_data['MadridTradeMark']['TradeMarkDetails']['@REGEDAT'], '2024-01-03')
        self.assertEqual(app_data['MadridTradeMark']['TradeMarkDetails']['@REGRDAT'], '2024-01-04')
        self.assertEqual(app_data['MadridTradeMark']['TradeMarkDetails']['@INTREGD'], '2024-01-05')

    def test_fix_pub_date(self):
        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    'ENN': {
                        '@PUBDATE': '20240101'
                    }
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['MadridTradeMark']['TradeMarkDetails']['ENN']['@PUBDATE'], '2024-01-01')

    def test_fix_basappd(self):
        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    'BASGR': {
                        'BASAPPGR': {
                            'BASAPPD': '20240101'
                        }
                    }
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['MadridTradeMark']['TradeMarkDetails']['BASGR']['BASAPPGR']['BASAPPD'], '2024-01-01')

    def test_fix_priappd(self):
        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    'PRIGR': {
                        'PRIAPPD': '20240101'
                    }
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['MadridTradeMark']['TradeMarkDetails']['PRIGR']['PRIAPPD'], '2024-01-01')


class ApplicationRawDataFSGeoFixerTestCase(TestCase):
    def setUp(self) -> None:
        self.fixer = ApplicationRawDataFSGeoFixer()

    def test_fix_product_description(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    'ProductDescription': 'Test Data'
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['Geo']['GeoDetails']['ProductDesc'], 'Test Data')
        self.assertNotIn('ProductDescription', app_data['Geo']['GeoDetails'])


class ApplicationRawDataFSCRFixerTestCase(TestCase):
    def setUp(self) -> None:
        self.fixer = ApplicationRawDataFSCRFixer()

    def test_fix_publication_date(self):
        app_data = {
            'Certificate': {
                'CopyrightDetails': {
                    'PublicationDetails': {
                        'Publication': {
                            'PublicationDate': '01.02.2024'
                        }
                    }
                }
            }
        }
        self.fixer.fix_data(app_data)
        self.assertEqual(app_data['Certificate']['CopyrightDetails']['PublicationDetails'][
                             'Publication']['PublicationDate'], '2024-02-01')
