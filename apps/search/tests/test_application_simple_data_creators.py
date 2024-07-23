from django.test import TestCase

from apps.search.models import IpcAppList
from apps.search.services.application_simple_data_creators import ApplicationSimpleDataTMCreator


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
