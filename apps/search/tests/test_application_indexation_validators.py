from django.test import TestCase
import datetime

from apps.search.services.application_indexation_validators import (ApplicationIndexationInvUMLDValidator,
                                                                    ApplicationIndexationIDValidator,
                                                                    ApplicationIndexationTMValidator)


class ApplicationIndexationTMValidatorTestCase(TestCase):

    def test_validate_publication_date(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicationNumber': 'm202400001',
                    'PublicationDetails': [
                        {
                            'PublicationDate': tomorrow.strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        validator = ApplicationIndexationTMValidator(app_data)
        with self.assertRaises(ValueError):
            validator.validate()

        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicationNumber': 'm202400001',
                    'PublicationDetails': [
                        {
                            'PublicationDate': datetime.date.today().strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        validator = ApplicationIndexationTMValidator(app_data)
        validator.validate()

    def test_validate_transaction_date(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicationNumber': 'm202400001',
                },
                'Transactions': {
                    'Transaction': [
                        {
                            '@bulletinDate': tomorrow.strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        validator = ApplicationIndexationTMValidator(app_data)
        with self.assertRaises(ValueError):
            validator.validate()

        app_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicationNumber': 'm202400001',
                },
                'Transactions': {
                    'Transaction': [
                        {
                            '@bulletinDate': datetime.date.today().strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        validator = ApplicationIndexationTMValidator(app_data)
        validator.validate()


class ApplicationIndexationIDValidatorTestCase(TestCase):

    def test_validate_publication_date(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        app_data = {
            'Design': {
                'DesignDetails': {
                    'DesignApplicationNumber': 's202400001',
                    'RecordPublicationDetails': [
                        {
                            'PublicationDate': tomorrow.strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        validator = ApplicationIndexationIDValidator(app_data)
        with self.assertRaises(ValueError):
            validator.validate()

        app_data = {
            'Design': {
                'DesignDetails': {
                    'DesignApplicationNumber': 's202400001',
                    'RecordPublicationDetails': [
                        {
                            'PublicationDate': datetime.date.today().strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        validator = ApplicationIndexationIDValidator(app_data)
        validator.validate()

    def test_validate_transaction_date(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        app_data = {
            'Design': {
                'DesignDetails': {
                    'DesignApplicationNumber': 's202400001'
                },
                'Transactions': {
                    'Transaction': [
                        {
                            '@bulletinDate': tomorrow.strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        validator = ApplicationIndexationIDValidator(app_data)
        with self.assertRaises(ValueError):
            validator.validate()

        app_data = {
            'Design': {
                'DesignDetails': {
                    'DesignApplicationNumber': 's202400001'
                },
                'Transactions': {
                    'Transaction': [
                        {
                            '@bulletinDate': datetime.date.today().strftime('%Y-%m-%d')
                        }
                    ]
                }
            }
        }
        validator = ApplicationIndexationIDValidator(app_data)
        validator.validate()


class ApplicationIndexationInvUMLDValidatorTestCase(TestCase):

    def test_validate_publication_date(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        app_data = {
            'Claim': {
                'I_21': 'a202400001',
                'I_43.D': [tomorrow.strftime('%Y-%m-%d')]
            }
        }
        validator = ApplicationIndexationInvUMLDValidator(app_data)
        with self.assertRaises(ValueError):
            validator.validate()

        app_data = {
            'Claim': {
                'I_21': 'a202400001',
                'I_43.D': [datetime.date.today().strftime('%Y-%m-%d')]
            }
        }
        validator = ApplicationIndexationInvUMLDValidator(app_data)
        validator.validate()
