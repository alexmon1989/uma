from django.test import TestCase

from apps.search.models import IpcAppList
from apps.search.services.application_simple_data_creators import (ApplicationSimpleDataTMCreator,
                                                                   ApplicationSimpleDataIDCreator,
                                                                   ApplicationSimpleDataInvUMLDCreator,
                                                                   ApplicationSimpleDataInvCertCreator,
                                                                   ApplicationSimpleDataMadridCreator,
                                                                   ApplicationSimpleDataGeoCreator,
                                                                   ApplicationSimpleDataCRCreator)


class ApplicationSimpleDataTMCreatorTestCase(TestCase):
    def setUp(self) -> None:
        self.simple_data_creator = ApplicationSimpleDataTMCreator()

    def test_get_obj_state(self):
        app = IpcAppList()
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['obj_state'], 1)

        app = IpcAppList(registration_number='0')
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['obj_state'], 1)

        app = IpcAppList(registration_number='123')
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['obj_state'], 2)

    def test_get_app_number(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicationNumber': 'm202400001'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_number'], 'm202400001')

    def test_get_app_date(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicationDate': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

        app_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            }
        }
        app = IpcAppList(app_date='2024-01-01', id_shedule_type=1)
        app.save()
        app.refresh_from_db()
        res = self.simple_data_creator.get_data(app, app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

        app = IpcAppList(app_input_date='2024-01-01', id_shedule_type=1)
        app.save()
        app.refresh_from_db()
        res = self.simple_data_creator.get_data(app, app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

    def test_get_protective_doc_number(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationNumber': '123456'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['protective_doc_number'], '123456')

    def test_get_rights_date(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationDate': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['rights_date'], '2024-01-01')

    def test_get_applicants(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicantDetails': {
                        'Applicant': [
                            {
                                'ApplicantAddressBook': {
                                    'FormattedNameAddress': {
                                        'Name': {
                                            'FreeFormatName': {
                                                'FreeFormatNameDetails': {
                                                    'FreeFormatNameLine': 'Іванов Іван Іванович',
                                                    'FreeFormatNameLineOriginal': 'Ivanov Ivan Ivanovich',
                                                },
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['applicant'],
            [
                {'name': 'Іванов Іван Іванович'},
                {'name': 'Ivanov Ivan Ivanovich'},
            ]
        )

    def test_get_owners(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'HolderDetails': {
                        'Holder': [
                            {
                                'HolderAddressBook': {
                                    'FormattedNameAddress': {
                                        'Name': {
                                            'FreeFormatName': {
                                                'FreeFormatNameDetails': {
                                                    'FreeFormatNameLine': 'Іванов Іван Іванович',
                                                    'FreeFormatNameLineOriginal': 'Ivanov Ivan Ivanovich',
                                                },
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['owner'],
            [
                {'name': 'Іванов Іван Іванович'},
                {'name': 'Ivanov Ivan Ivanovich'},
            ]
        )

    def test_get_title(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['title'], '')

        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'WordMarkSpecification': {
                        'MarkSignificantVerbalElement': [
                            {
                                '#text': 'test',
                            },
                            {
                                '#text': 'data',
                            },
                        ]
                    }
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['title'], 'test, data')

    def test_get_agents(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RepresentativeDetails': {
                        'Representative': [
                            {
                                'RepresentativeAddressBook': {
                                    'FormattedNameAddress': {
                                        'Address': {
                                            'FreeFormatAddress': {
                                                'FreeFormatAddressLine': 'Адреса'
                                            }
                                        },
                                        'Name': {
                                            'FreeFormatName': {
                                                'FreeFormatNameDetails': {
                                                    'FreeFormatNameDetails': {
                                                        'FreeFormatNameLine': 'Іванов Іван Іванович'
                                                    }
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['agent'],
            [
                {'name': 'Іванов Іван Іванович, Адреса'},
            ]
        )

    def test_get_registration_status_color(self):
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'registration_status_color': 'green'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
        self.assertEqual(res['registration_status_color'], 'green')

        red_transaction_types = [
            'TerminationNoRenewalFee',
            'TotalTerminationByOwner',
            'TotalInvalidationByCourt',
            'TotalTerminationByCourt',
            'TotalInvalidationByAppeal',
        ]
        for r_t in red_transaction_types:
            app_data = {
                'TradeMark': {
                    'TrademarkDetails': {},
                    "Transactions": {
                        "Transaction": [
                            {
                                "@type": 'Test Data'
                            },
                            {
                                "@type": r_t
                            }
                        ]
                    }
                }
            }
            res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
            self.assertEqual(res['registration_status_color'], 'red')

        app_data = {
            'TradeMark': {
                'TrademarkDetails': {},
                "Transactions": {
                    "Transaction": [
                        {
                            "@type": 'Test Data'
                        }
                    ]
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
        self.assertEqual(res['registration_status_color'], 'green')


class ApplicationSimpleDataIDCreatorTestCase(TestCase):
    def setUp(self) -> None:
        self.simple_data_creator = ApplicationSimpleDataIDCreator()

    def test_get_obj_state(self):
        app = IpcAppList()
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['obj_state'], 1)

        app = IpcAppList(registration_number='0')
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['obj_state'], 1)

        app = IpcAppList(registration_number='123')
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['obj_state'], 2)

    def test_get_app_number(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'DesignApplicationNumber': 's202400001'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_number'], 's202400001')

    def test_get_app_date(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'DesignApplicationDate': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

        app_data = {
            'Design': {
                'DesignDetails': {}
            }
        }
        app = IpcAppList(app_date='2024-01-01', id_shedule_type=1)
        app.save()
        app.refresh_from_db()
        res = self.simple_data_creator.get_data(app, app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

        app = IpcAppList(app_input_date='2024-01-01', id_shedule_type=1)
        app.save()
        app.refresh_from_db()
        res = self.simple_data_creator.get_data(app, app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

    def test_get_protective_doc_number(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'RegistrationNumber': '123456'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['protective_doc_number'], '123456')

    def test_get_rights_date(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'RecordEffectiveDate': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['rights_date'], '2024-01-01')

    def test_get_applicants(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'ApplicantDetails': {
                        'Applicant': [
                            {
                                'ApplicantAddressBook': {
                                    'FormattedNameAddress': {
                                        'Name': {
                                            'FreeFormatName': {
                                                'FreeFormatNameDetails': {
                                                    'FreeFormatNameLine': 'Іванов Іван Іванович'
                                                },
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['applicant'],
            [
                {'name': 'Іванов Іван Іванович'}
            ]
        )

    def test_get_owners(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'HolderDetails': {
                        'Holder': [
                            {
                                'HolderAddressBook': {
                                    'FormattedNameAddress': {
                                        'Name': {
                                            'FreeFormatName': {
                                                'FreeFormatNameDetails': {
                                                    'FreeFormatNameLine': 'Іванов Іван Іванович'
                                                },
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['owner'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_title(self):
        app_data = {
            'Design': {
                'DesignDetails': {}
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['title'], '')

        app_data = {
            'Design': {
                'DesignDetails': {
                    'DesignTitle': 'Test Data'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['title'], 'Test Data')

    def test_get_agents(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'RepresentativeDetails': {
                        'Representative': [
                            {
                                'RepresentativeAddressBook': {
                                    'FormattedNameAddress': {
                                        'Address': {
                                            'FreeFormatAddress': {
                                                'FreeFormatAddressLine': 'Адреса'
                                            }
                                        },
                                        'Name': {
                                            'FreeFormatName': {
                                                'FreeFormatNameDetails': {
                                                    'FreeFormatNameLine': 'Іванов Іван Іванович'
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['agent'],
            [
                {'name': 'Іванов Іван Іванович, Адреса'},
            ]
        )

    def test_get_inventors(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    "DesignerDetails": {
                        "Designer": [
                            {
                                "DesignerAddressBook": {
                                    "FormattedNameAddress": {
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іванов Іван Іванович"
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['inventor'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_registration_status_color(self):
        app_data = {
            'Design': {
                'DesignDetails': {
                    'registration_status_color': 'green'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
        self.assertEqual(res['registration_status_color'], 'green')

        red_transaction_types = [
            'Termination',
            'TerminationByAppeal',
            'TerminationNoRenewalFee',
            'TotalInvalidationByAppeal',
            'TotalInvalidationByCourt',
            'TotalTerminationByOwner',
        ]
        for r_t in red_transaction_types:
            app_data = {
                'Design': {
                    'DesignDetails': {},
                    "Transactions": {
                        "Transaction": [
                            {
                                "@type": 'Test Data'
                            },
                            {
                                "@type": r_t
                            }
                        ]
                    }
                }
            }
            res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
            self.assertEqual(res['registration_status_color'], 'red')

        app_data = {
            'Design': {
                'DesignDetails': {},
                "Transactions": {
                    "Transaction": [
                        {
                            "@type": 'Test Data'
                        }
                    ]
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
        self.assertEqual(res['registration_status_color'], 'green')


class ApplicationSimpleDataInvUMLDCreatorTestCase(TestCase):

    def setUp(self) -> None:
        self.simple_data_creator = ApplicationSimpleDataInvUMLDCreator()

    def test_get_obj_state(self):
        app = IpcAppList()
        res = self.simple_data_creator.get_data(app, {'Claim': {}})
        self.assertEqual(res['obj_state'], 1)

        app = IpcAppList(registration_number='0')
        res = self.simple_data_creator.get_data(app, {'Claim': {}})
        self.assertEqual(res['obj_state'], 1)

        app = IpcAppList(registration_number='123')
        res = self.simple_data_creator.get_data(app, {'Patent': {}})
        self.assertEqual(res['obj_state'], 2)

    def test_get_app_number(self):
        app_data = {
            'Claim': {
                'I_21': 'a202400001'
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_number'], 'a202400001')

    def test_get_app_date(self):
        app_data = {
            'Claim': {
                'I_22': '2024-01-01'
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

    def test_get_protective_doc_number(self):
        app_data = {
            'Patent': {
                'I_11': '12345'
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['protective_doc_number'], '12345')

    def test_get_rights_date(self):
        app_data = {
            'Patent': {
                'I_24': '2024-01-01'
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['rights_date'], '2024-01-01')

        app_data = {
            'Patent': {
                'I_24': '1899-12-30'
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertIsNone(res['rights_date'])

    def test_get_applicant(self):
        app_data = {
            'Patent': {
                "I_71": [
                    {
                        "I_71.N.U": "Іванов Іван Іванович",
                        "I_71.C.U": "AT"
                    }
                ]
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['applicant'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_inventor(self):
        app_data = {
            'Patent': {
                "I_72": [
                    {
                        "I_72.N.U": "Іванов Іван Іванович",
                        "I_72.C.U": "AT"
                    }
                ]
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['inventor'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_owner(self):
        app_data = {
            'Patent': {
                "I_73": [
                    {
                        "I_73.N": "Іванов Іван Іванович",
                        "I_73.C": "AT"
                    },
                    {
                        "EDRPOU": "12345",
                        "I_73.N": "Петров Петро Петрович",
                        "I_73.C": "AT"
                    }
                ]
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['owner'],
            [
                {'name': 'Іванов Іван Іванович'},
                {'name': 'Петров Петро Петрович'},
            ]
        )

    def test_get_title(self):
        app_data = {
            'Patent': {
                "I_54": [
                    {
                        "I_54.U": "Тестові дані"
                    },
                    {
                        "I_54.E": "Test Data"
                    }
                ]
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['title'], ['Тестові дані', 'Test Data'])

    def test_get_agent(self):
        app_data = {
            'Patent': {
                "I_74": 'Іванов Іван Іванович'
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['agent'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_registration_status_color(self):
        app_data = {
            'Document': {
                'RegistrationStatus': 'A'
            },
            'Patent': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'green')

        app_data = {
            'Document': {
                'RegistrationStatus': 'N'
            },
            'Patent': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'red')

        app_data = {
            'Document': {
                'RegistrationStatus': 'T'
            },
            'Patent': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'yellow')

        app_data = {
            'Document': {
                'RegistrationStatus': 'OTHER'
            },
            'Patent': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'red')

        app_data = {
            'Patent': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'red')


class ApplicationSimpleDataInvCertCreatorTestCase(TestCase):

    def setUp(self) -> None:
        self.simple_data_creator = ApplicationSimpleDataInvCertCreator()

    def test_get_obj_state(self):
        app = IpcAppList()
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['obj_state'], 2)

    def test_get_protective_doc_number(self):
        app_data = {
            'Patent_Certificate': {
                'I_11': '12345'
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['protective_doc_number'], '12345')

    def test_get_owner(self):
        app_data = {
            'Patent_Certificate': {
                "I_73": [
                    {
                        "N.U": "Іванов Іван Іванович",
                        "A.U": "Test Data",
                        "C.U": "UA"
                    }
                ]
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['owner'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_title(self):
        app_data = {
            'Patent_Certificate': {
                "I_95": 'Test Data'
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['title'], 'Test Data')

    def test_get_registration_status_color(self):
        app_data = {
            'Document': {
                'RegistrationStatus': 'A'
            },
            'Patent_Certificate': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'green')

        app_data = {
            'Document': {
                'RegistrationStatus': 'N'
            },
            'Patent_Certificate': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'red')

        app_data = {
            'Document': {
                'RegistrationStatus': 'T'
            },
            'Patent_Certificate': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'yellow')

        app_data = {
            'Document': {
                'RegistrationStatus': 'OTHER'
            },
            'Patent_Certificate': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'red')

        app_data = {
            'Patent_Certificate': {}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'red')


class ApplicationSimpleDataMadridCreatorTestCase(TestCase):

    def setUp(self) -> None:
        self.simple_data_creator = ApplicationSimpleDataMadridCreator()

    def test_get_obj_state(self):
        app = IpcAppList()
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['obj_state'], 2)

    def test_get_protective_doc_number(self):
        app = IpcAppList(registration_number='12345')
        res = self.simple_data_creator.get_data(app, {})
        self.assertEqual(res['protective_doc_number'], app.registration_number)

    def test_get_rights_date(self):
        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    '@INTREGD': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
        self.assertEqual(res['rights_date'], '2024-01-01')

    def test_get_owner(self):
        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    "HOLGR": {
                        "NAME": {
                            "NAMEL": "Іванов Іван Іванович"
                        }
                    }
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
        self.assertEqual(
            res['owner'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_agent(self):
        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    "REPGR": {
                        "NAME": {
                            "NAMEL": "Іванов Іван Іванович"
                        }
                    }
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
        self.assertEqual(
            res['agent'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_title(self):
        app_data = {
            'MadridTradeMark': {
                'TradeMarkDetails': {
                    "IMAGE": {
                        "@TEXT": "Test Data"
                    }
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(registration_number='12345'), app_data)
        self.assertEqual(res['title'], 'Test Data')


class ApplicationSimpleDataGeoCreatorTestCase(TestCase):

    def setUp(self) -> None:
        self.simple_data_creator = ApplicationSimpleDataGeoCreator()

    def test_get_obj_state(self):
        app = IpcAppList()
        res = self.simple_data_creator.get_data(app, {'Claim': {}})
        self.assertEqual(res['obj_state'], 1)

        app = IpcAppList(registration_number='0')
        res = self.simple_data_creator.get_data(app, {'Claim': {}})
        self.assertEqual(res['obj_state'], 1)

        app = IpcAppList(registration_number='123')
        res = self.simple_data_creator.get_data(app, {'Patent': {}})
        self.assertEqual(res['obj_state'], 2)

    def test_get_app_number(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    'ApplicationNumber': 'i202400001'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_number'], 'i202400001')

    def test_get_app_date(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    'ApplicationDate': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

    def test_get_protective_doc_number(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    'RegistrationNumber': '123456'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['protective_doc_number'], '123456')

    def test_get_rights_date(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    'RegistrationDate': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['rights_date'], '2024-01-01')

    def test_get_applicants(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    "ApplicantDetails": {
                        "Applicant": [
                            {
                                "ApplicantAddressBook": {
                                    "FormattedNameAddress": {
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іванов Іван Іванович",
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['applicant'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_owners(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    "HolderDetails": {
                        "Holder": [
                            {
                                "HolderAddressBook": {
                                    "FormattedNameAddress": {
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іванов Іван Іванович"
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['owner'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_agents(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    "RepresentativeDetails": {
                        "Representative": [
                            {
                                "RepresentativeAddressBook": {
                                    "FormattedNameAddress": {
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іванов Іван Іванович"
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['agent'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_title(self):
        app_data = {
            'Geo': {
                'GeoDetails': {
                    "Indication": "Test Data"
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['title'], 'Test Data')


class ApplicationSimpleDataCRCreatorTestCase(TestCase):

    def setUp(self) -> None:
        self.simple_data_creator = ApplicationSimpleDataCRCreator()

    def test_get_obj_state(self):
        app = IpcAppList()
        res = self.simple_data_creator.get_data(app, {'Certificate': {'CopyrightDetails': {}}})
        self.assertEqual(res['obj_state'], 2)

    def test_get_app_number(self):
        app_data = {
            'Certificate': {
                'CopyrightDetails': {
                    'ApplicationNumber': 'i202400001'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_number'], 'i202400001')

    def test_get_app_date(self):
        app_data = {
            'Certificate': {
                'CopyrightDetails': {
                    'ApplicationDate': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['app_date'], '2024-01-01')

    def test_get_protective_doc_number(self):
        app_data = {
            'Certificate': {
                'CopyrightDetails': {
                    'RegistrationNumber': '123456'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['protective_doc_number'], '123456')

    def test_get_rights_date(self):
        app_data = {
            'Certificate': {
                'CopyrightDetails': {
                    'RegistrationDate': '2024-01-01'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['rights_date'], '2024-01-01')

    def test_get_owners(self):
        app_data = {
            'Certificate': {
                'CopyrightDetails': {
                    "AuthorDetails": {
                        "Author": [
                            {
                                "AuthorAddressBook": {
                                    "FormattedNameAddress": {
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іванов Іван Іванович"
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
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(
            res['owner'],
            [
                {'name': 'Іванов Іван Іванович'},
            ]
        )

    def test_get_title(self):
        app_data = {
            'Certificate': {
                'CopyrightDetails': {
                    "Name": 'Test Data'
                }
            }
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['title'], 'Test Data')

    def test_get_registration_status_color(self):
        app_data = {
            'Document': {
                'RegistrationStatus': 'Реєстрація недійсна'
            },
            'Certificate': {'CopyrightDetails': {}}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'red')

        app_data = {
            'Document': {
                'RegistrationStatus': 'Свідоцтво видано'
            },
            'Certificate': {'CopyrightDetails': {}}
        }
        res = self.simple_data_creator.get_data(IpcAppList(), app_data)
        self.assertEqual(res['registration_status_color'], 'green')
