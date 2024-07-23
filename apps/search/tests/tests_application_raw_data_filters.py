import json

from django.test import TestCase

from apps.search.models import ObjType, AppLimited
from apps.search.services.application_raw_data_filters import (ApplicationRawDataTMLimitedFilter,
                                                               ApplicationRawDataIDLimitedFilter,
                                                               ApplicationRawDataInvUMLDLimitedFilter,
                                                               ApplicationRawDataCRLimitedFilter,
                                                               ApplicationRawDataDecisionLimitedFilter)


class ApplicationRawDataTMLimitedFilterTestCase(TestCase):

    def setUp(self) -> None:
        self.filter = ApplicationRawDataTMLimitedFilter()
        self.app_data = {
            'Document': {},
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicantDetails': {},
                    'HolderDetails': {},
                    'CorrespondenceAddress': {},
                    'MarkImageDetails': {
                        'MarkImage': {
                            'MarkImageColourClaimedText': 'test data',
                            'MarkImageFilename': 'test data'
                        }
                    },
                }
            }
        }

    def test_filter_data_not_limited(self):
        self.filter.filter_data(self.app_data)
        self.assertIn('ApplicantDetails', self.app_data['TradeMark']['TrademarkDetails'])
        self.assertIn('HolderDetails', self.app_data['TradeMark']['TrademarkDetails'])
        self.assertIn('CorrespondenceAddress', self.app_data['TradeMark']['TrademarkDetails'])
        self.assertIn(
            'MarkImageColourClaimedText',
            self.app_data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']
        )
        self.assertIn(
            'MarkImageFilename',
            self.app_data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']
        )

    def test_filter_data_limited(self):
        self.app_data['Document']['is_limited'] = True
        self.filter.filter_data(self.app_data)
        self.assertNotIn('ApplicantDetails', self.app_data['TradeMark']['TrademarkDetails'])
        self.assertNotIn('HolderDetails', self.app_data['TradeMark']['TrademarkDetails'])
        self.assertNotIn('CorrespondenceAddress', self.app_data['TradeMark']['TrademarkDetails'])
        self.assertNotIn(
            'MarkImageColourClaimedText',
            self.app_data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']
        )
        self.assertNotIn(
            'MarkImageFilename',
            self.app_data['TradeMark']['TrademarkDetails']['MarkImageDetails']['MarkImage']
        )


class ApplicationRawDataIDLimitedFilterTestCase(TestCase):

    def setUp(self) -> None:
        self.filter = ApplicationRawDataIDLimitedFilter()
        self.app_data = {
            'Document': {},
            'Design': {
                'DesignDetails': {
                    'ApplicantDetails': {},
                    'DesignerDetails': {},
                    'HolderDetails': {},
                    'CorrespondenceAddress': {},
                    'DesignSpecimenDetails': {},
                }
            }
        }

    def test_filter_data_not_limited(self):
        self.filter.filter_data(self.app_data)
        self.assertIn('ApplicantDetails', self.app_data['Design']['DesignDetails'])
        self.assertIn('HolderDetails', self.app_data['Design']['DesignDetails'])
        self.assertIn('HolderDetails', self.app_data['Design']['DesignDetails'])
        self.assertIn('CorrespondenceAddress', self.app_data['Design']['DesignDetails'])
        self.assertIn('DesignSpecimenDetails', self.app_data['Design']['DesignDetails'])

    def test_filter_data_limited(self):
        self.app_data['Document']['is_limited'] = True
        self.filter.filter_data(self.app_data)
        self.assertNotIn('ApplicantDetails', self.app_data['Design']['DesignDetails'])
        self.assertNotIn('HolderDetails', self.app_data['Design']['DesignDetails'])
        self.assertNotIn('HolderDetails', self.app_data['Design']['DesignDetails'])
        self.assertNotIn('CorrespondenceAddress', self.app_data['Design']['DesignDetails'])
        self.assertNotIn('DesignSpecimenDetails', self.app_data['Design']['DesignDetails'])


class ApplicationRawDataInvUMLDLimitedFilterTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.obj_type = ObjType.objects.create(obj_type_ua='Винаходи')

    def setUp(self) -> None:
        self.filter = ApplicationRawDataInvUMLDLimitedFilter()
        self.app_data = {
            'Document': {
                'idObjType': self.obj_type.pk
            },
            'Patent': {
                'I_21': 'a202400001',
                'AB': 'Test Data',
                'CL': 'Test Data',
                'DE': 'Test Data',
                'I_71': 'Test Data',
                'I_72': 'Test Data',
                'I_73': 'Test Data',
                'I_98': 'Test Data',
                'I_98_Index': 'Test Data',
            }
        }

    def test_filter_data_not_limited(self):
        self.filter.filter_data(self.app_data)
        self.assertIn('AB', self.app_data['Patent'])
        self.assertIn('CL', self.app_data['Patent'])
        self.assertIn('DE', self.app_data['Patent'])
        self.assertIn('I_71', self.app_data['Patent'])
        self.assertIn('I_72', self.app_data['Patent'])
        self.assertIn('I_73', self.app_data['Patent'])
        self.assertIn('I_98', self.app_data['Patent'])
        self.assertIn('I_98_Index', self.app_data['Patent'])

    def test_filter_limited_default(self):
        self.app_data['Document']['is_limited'] = True
        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number=self.app_data['Patent']['I_21'],
            obj_type_id=self.app_data['Document']['idObjType']
        )
        self.filter.filter_data(self.app_data)
        self.assertNotIn('AB', self.app_data['Patent'])
        self.assertNotIn('CL', self.app_data['Patent'])
        self.assertNotIn('DE', self.app_data['Patent'])
        self.assertNotIn('I_71', self.app_data['Patent'])
        self.assertNotIn('I_72', self.app_data['Patent'])
        self.assertNotIn('I_73', self.app_data['Patent'])
        self.assertNotIn('I_98', self.app_data['Patent'])
        self.assertNotIn('I_98_Index', self.app_data['Patent'])

    def test_filter_limited_not_default(self):
        self.app_data['Document']['is_limited'] = True
        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number=self.app_data['Patent']['I_21'],
            obj_type_id=self.app_data['Document']['idObjType'],
            settings_json=json.dumps({
                'AB': True,
                'CL': True,
                'DE': True,
                'I_71': True,
                'I_72': True,
                'I_73': True,
                'I_98': True,
                'I_98_Index': True,
            })
        )
        self.filter.filter_data(self.app_data)
        self.assertIn('AB', self.app_data['Patent'])
        self.assertIn('CL', self.app_data['Patent'])
        self.assertIn('DE', self.app_data['Patent'])
        self.assertIn('I_71', self.app_data['Patent'])
        self.assertIn('I_72', self.app_data['Patent'])
        self.assertIn('I_73', self.app_data['Patent'])
        self.assertIn('I_98', self.app_data['Patent'])
        self.assertIn('I_98_Index', self.app_data['Patent'])

        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number=self.app_data['Patent']['I_21'],
            obj_type_id=self.app_data['Document']['idObjType'],
            settings_json=json.dumps({
                'AB': False,
                'CL': False,
                'DE': False,
                'I_71': False,
                'I_72': False,
                'I_73': False,
                'I_98': False,
                'I_98_Index': False,
            })
        )
        self.filter.filter_data(self.app_data)
        self.assertNotIn('AB', self.app_data['Patent'])
        self.assertNotIn('CL', self.app_data['Patent'])
        self.assertNotIn('DE', self.app_data['Patent'])
        self.assertNotIn('I_71', self.app_data['Patent'])
        self.assertNotIn('I_72', self.app_data['Patent'])
        self.assertNotIn('I_73', self.app_data['Patent'])
        self.assertNotIn('I_98', self.app_data['Patent'])
        self.assertNotIn('I_98_Index', self.app_data['Patent'])


class ApplicationRawDataCRLimitedFilterTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.obj_type = ObjType.objects.create(obj_type_ua='Авторське право')

    def setUp(self) -> None:
        self.filter = ApplicationRawDataCRLimitedFilter()
        self.app_data = {
            'Document': {
                'idObjType': self.obj_type.pk
            },
            'Certificate': {
                'CopyrightDetails': {
                    'ApplicationNumber': 'c202400001',
                    'AuthorDetails': {},
                    'Annotation': 'Test Data',
                    'ApplicantDetails': {},
                    'CopyrightObjectKindDetails': {},
                    'EmployerDetails': {},
                    'HolderDetails': {},
                    'PromulgationData': 'Test Data',
                    'RegistrationKind': 'Test Data',
                    'RegistrationKindCode': 'Test Data',
                    'RegistrationOfficeCode': 'Test Data',
                    'RepresentativeDetails': {},
                    'Name': 'Test Data',
                    'NameShort': 'Test Data',
                }
            }
        }

    def test_filter_data_not_limited(self):
        self.filter.filter_data(self.app_data)
        self.assertIn('AuthorDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('Annotation', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('ApplicantDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('CopyrightObjectKindDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('EmployerDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('HolderDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('PromulgationData', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RegistrationKind', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RegistrationKindCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RegistrationOfficeCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RegistrationKindCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RepresentativeDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('Name', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('NameShort', self.app_data['Certificate']['CopyrightDetails'])

    def test_filter_limited_default(self):
        self.app_data['Document']['is_limited'] = True
        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number=self.app_data['Certificate']['CopyrightDetails']['ApplicationNumber'],
            obj_type_id=self.app_data['Document']['idObjType']
        )
        self.filter.filter_data(self.app_data)
        self.assertNotIn('AuthorDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('Annotation', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('ApplicantDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('CopyrightObjectKindDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('EmployerDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('HolderDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('PromulgationData', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RegistrationKind', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RegistrationKindCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RegistrationOfficeCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RegistrationKindCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RepresentativeDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('Name', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('NameShort', self.app_data['Certificate']['CopyrightDetails'])

    def test_filter_limited_not_default(self):
        self.app_data['Document']['is_limited'] = True
        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number=self.app_data['Certificate']['CopyrightDetails']['ApplicationNumber'],
            obj_type_id=self.app_data['Document']['idObjType'],
            settings_json=json.dumps({
                'AuthorDetails': True,
                'Annotation': True,
                'ApplicantDetails': True,
                'CopyrightObjectKindDetails': True,
                'EmployerDetails': True,
                'HolderDetails': True,
                'PromulgationData': True,
                'RegistrationKind': True,
                'RegistrationKindCode': True,
                'RegistrationOfficeCode': True,
                'RepresentativeDetails': True,
                'Name': True,
                'NameShort': True,
            })
        )
        self.filter.filter_data(self.app_data)
        self.assertIn('AuthorDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('Annotation', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('ApplicantDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('CopyrightObjectKindDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('EmployerDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('HolderDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('PromulgationData', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RegistrationKind', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RegistrationKindCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RegistrationOfficeCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RegistrationKindCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('RepresentativeDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('Name', self.app_data['Certificate']['CopyrightDetails'])
        self.assertIn('NameShort', self.app_data['Certificate']['CopyrightDetails'])

        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number=self.app_data['Certificate']['CopyrightDetails']['ApplicationNumber'],
            obj_type_id=self.app_data['Document']['idObjType'],
            settings_json=json.dumps({
                'AuthorDetails': False,
                'Annotation': False,
                'ApplicantDetails': False,
                'CopyrightObjectKindDetails': False,
                'EmployerDetails': False,
                'HolderDetails': False,
                'PromulgationData': False,
                'RegistrationKind': False,
                'RegistrationKindCode': False,
                'RegistrationOfficeCode': False,
                'RepresentativeDetails': False,
                'Name': False,
                'NameShort': False,
            })
        )
        self.filter.filter_data(self.app_data)
        self.assertNotIn('AuthorDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('Annotation', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('ApplicantDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('CopyrightObjectKindDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('EmployerDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('HolderDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('PromulgationData', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RegistrationKind', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RegistrationKindCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RegistrationOfficeCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RegistrationKindCode', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('RepresentativeDetails', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('Name', self.app_data['Certificate']['CopyrightDetails'])
        self.assertNotIn('NameShort', self.app_data['Certificate']['CopyrightDetails'])


class ApplicationRawDataDecisionLimitedFilterTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.obj_type = ObjType.objects.create(obj_type_ua='Договір про передачу права на використання твору')

    def setUp(self) -> None:
        self.filter = ApplicationRawDataDecisionLimitedFilter()
        self.app_data = {
            'Document': {
                'idObjType': self.obj_type.pk
            },
            'Decision': {
                'DecisionDetails': {
                    'ApplicationNumber': 'r202400001',
                    'RegistrationNumber': 'Test Data',
                    'RegistrationDate': 'Test Data',
                    'PublicationDetails': {},
                    'Name': 'Test Data',
                    'NameShort': 'Test Data',

                    'Annotation': 'Test Data',
                    'ApplicantDetails': {},
                    'ApplicationDate': 'Test Data',
                    'AuthorDetails': 'Test Data',
                    'CopyrightObjectKindDetails': 'Test Data',
                    'DocFlow': {},
                    'LicenseeDetails': {
                        'Licensee': [
                            {
                                'LicenseeAddressBook': {
                                    'FormattedNameAddress': {
                                        'Address': 'Test Data 1',
                                        'Name': 'Test Data 1',
                                    }
                                }
                            }
                        ]
                    },
                    'LicensorDetails': {
                        'Licensor': [
                            {
                                'LicensorAddressBook': {
                                    'FormattedNameAddress': {
                                        'Address': 'Test Data',
                                        'Name': 'Test Data',
                                    }
                                }
                            }
                        ]
                    },
                    'RegistrationKind': 'Test Data',
                    'RegistrationKindCode': 'Test Data',
                    'RegistrationOfficeCode': 'Test Data',
                    'RepresentativeDetails': {},
                }
            }
        }

    def test_filter_data_not_limited(self):
        self.filter.filter_data(self.app_data)
        self.assertIn('ApplicationNumber', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationNumber', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationDate', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('PublicationDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('Name', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('NameShort', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('Annotation', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('ApplicantDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('ApplicationDate', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('AuthorDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('CopyrightObjectKindDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('DocFlow', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('LicenseeDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('LicensorDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationKind', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationKindCode', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationOfficeCode', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RepresentativeDetails', self.app_data['Decision']['DecisionDetails'])

    def test_filter_limited_default(self):
        self.app_data['Document']['is_limited'] = True
        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number='r202400001',
            obj_type_id=self.app_data['Document']['idObjType']
        )
        self.filter.filter_data(self.app_data)
        self.assertIn('RegistrationNumber', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationDate', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('PublicationDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('Name', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('NameShort', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('ApplicationNumber', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('Annotation', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('ApplicantDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('ApplicationDate', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('AuthorDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('CopyrightObjectKindDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('DocFlow', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('LicenseeDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('LicensorDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RegistrationKind', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RegistrationKindCode', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RegistrationOfficeCode', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RepresentativeDetails', self.app_data['Decision']['DecisionDetails'])

    def test_filter_limited_not_default(self):
        self.app_data['Document']['is_limited'] = True
        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number='r202400001',
            obj_type_id=self.app_data['Document']['idObjType'],
            settings_json=json.dumps({
                'RegistrationNumber': True,
                'RegistrationDate': True,
                'PublicationDetails': True,
                'Name': True,
                'NameShort': True,
                'ApplicationNumber': True,
                'Annotation': True,
                'ApplicantDetails': True,
                'ApplicationDate': True,
                'AuthorDetails': True,
                'CopyrightObjectKindDetails': True,
                'DocFlow': True,
                'LicenseeDetails': {'Address': True, 'Name': True},
                'LicensorDetails': {'Address': True, 'Name': True},
                'RegistrationKind': True,
                'RegistrationKindCode': True,
                'RegistrationOfficeCode': True,
                'RepresentativeDetails': True,
            })
        )
        self.filter.filter_data(self.app_data)
        self.assertIn('RegistrationNumber', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationDate', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('PublicationDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('Name', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('NameShort', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('ApplicationNumber', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('Annotation', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('ApplicantDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('ApplicationDate', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('AuthorDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('CopyrightObjectKindDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('DocFlow', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('LicenseeDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('LicensorDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationKind', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationKindCode', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RegistrationOfficeCode', self.app_data['Decision']['DecisionDetails'])
        self.assertIn('RepresentativeDetails', self.app_data['Decision']['DecisionDetails'])

        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number='r202400001',
            obj_type_id=self.app_data['Document']['idObjType'],
            settings_json=json.dumps({
                'RegistrationNumber': False,
                'RegistrationDate': False,
                'PublicationDetails': False,
                'Name': False,
                'NameShort': False,
                'ApplicationNumber': False,
                'Annotation': False,
                'ApplicantDetails': False,
                'ApplicationDate': False,
                'AuthorDetails': False,
                'CopyrightObjectKindDetails': False,
                'DocFlow': False,
                'LicenseeDetails': False,
                'LicensorDetails': False,
                'RegistrationKind': False,
                'RegistrationKindCode': False,
                'RegistrationOfficeCode': False,
                'RepresentativeDetails': False,
            })
        )
        self.filter.filter_data(self.app_data)
        self.assertNotIn('RegistrationNumber', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RegistrationDate', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('PublicationDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('Name', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('NameShort', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('ApplicationNumber', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('Annotation', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('ApplicantDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('ApplicationDate', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('AuthorDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('CopyrightObjectKindDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('DocFlow', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('LicenseeDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('LicensorDetails', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RegistrationKind', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RegistrationKindCode', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RegistrationOfficeCode', self.app_data['Decision']['DecisionDetails'])
        self.assertNotIn('RepresentativeDetails', self.app_data['Decision']['DecisionDetails'])

    def test_filter_limited_license(self):
        self.app_data['Document']['is_limited'] = True
        AppLimited.objects.all().delete()
        AppLimited.objects.create(
            app_number='r202400001',
            obj_type_id=self.app_data['Document']['idObjType'],
            settings_json=json.dumps({
                'LicenseeDetails': {'Address': False, 'Name': False},
                'LicensorDetails': {'Address': False, 'Name': False}
            })
        )
        self.filter.filter_data(self.app_data)
        for item in self.app_data['Decision']['DecisionDetails']['LicenseeDetails']['Licensee']:
            self.assertNotIn('Address', item['LicenseeAddressBook']['FormattedNameAddress'])
            self.assertNotIn('Name', item['LicenseeAddressBook']['FormattedNameAddress'])
        for item in self.app_data['Decision']['DecisionDetails']['LicensorDetails']['Licensor']:
            self.assertNotIn('Address', item['LicensorAddressBook']['FormattedNameAddress'])
            self.assertNotIn('Name', item['LicensorAddressBook']['FormattedNameAddress'])
