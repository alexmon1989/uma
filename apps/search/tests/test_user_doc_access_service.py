from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser, Group
from unittest.mock import MagicMock, patch

from apps.my_auth.models import CertificateOwner
from apps.search.services import UserDocAccessService


class UserDocAccessServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', first_name='Іван', last_name='Іванов')

    def _create_cert_owner(self, full_name='Іванов Іван Іванович', edrpou='12345678'):
        cert = CertificateOwner.objects.create(
            user=self.user,
            pszSubjFullName=full_name,
            pszSubjEDRPOUCode=edrpou
        )
        return cert

    def test_anonymous_user_has_no_access(self):
        user = AnonymousUser()
        hit = {'Document': {'idObjType': 4}}
        service = UserDocAccessService(user, hit)
        self.assertFalse(service.has_access())

    def test_vip_user_has_access(self):
        self.user.is_vip = MagicMock(return_value=True)
        hit = {'Document': {'idObjType': 4}}
        service = UserDocAccessService(self.user, hit)
        self.assertTrue(service.has_access())

    @patch('apps.search.utils.is_app_limited')
    def test_nazk_user_access(self, mock_is_app_limited):
        nazk_group = Group.objects.create(name='НАЗК')
        self.user.groups.add(nazk_group)
        hit = {'Document': {'idObjType': 1}}

        # Необмежена заявка
        mock_is_app_limited.return_value = False
        service = UserDocAccessService(self.user, hit)
        self.assertTrue(service.has_access())

        # Обмежена заявка
        mock_is_app_limited.return_value = True
        service = UserDocAccessService(self.user, hit)
        self.assertFalse(service.has_access())

    def test_inv_um_ld_edrpou_match_patent_i71(self):
        """idObjType in (1, 2, 3): перевірка за Patent.I_71"""
        self._create_cert_owner(edrpou='12345678')
        for obj_type in (1, 2, 3):
            hit = {
                'Document': {'idObjType': obj_type},
                'Patent': {
                    'I_71': [{'I_71.N': 'ТОВ Ромашка', 'EDRPOU': '12345678'}]
                }
            }
            self.assertTrue(UserDocAccessService(self.user, hit).has_access())

    def test_inv_um_ld_edrpou_match_claim_i73(self):
        """idObjType in (1, 2, 3): перевірка за Claim.I_73"""
        self._create_cert_owner(edrpou='12345678')
        hit = {
            'Document': {'idObjType': 2},
            'Claim': {
                'I_73': [{'I_73.N': 'ТОВ Волошка', 'EDRPOU': '12345678'}]
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit).has_access())

    def test_tm_edrpou_match(self):
        """idObjType == 4: перевірка за ApplicantDetails та HolderDetails"""
        self._create_cert_owner(edrpou='12345678')
        # Applicant
        hit_applicant = {
            'Document': {'idObjType': 4},
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicantDetails': {
                        'Applicant': [
                            {
                                'ApplicantAddressBook': {
                                    'FormattedNameAddress': {
                                        'Name': {
                                            'FreeFormatName': {'EDRPOU': '12345678'}
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit_applicant).has_access())

        # Holder
        hit_holder = {
            'Document': {'idObjType': 4},
            'TradeMark': {
                'TrademarkDetails': {
                    'HolderDetails': {
                        'Holder': [
                            {
                                'HolderAddressBook': {
                                    'FormattedNameAddress': {
                                        'Name': {
                                            'FreeFormatName': {'EDRPOU': '12345678'}
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit_holder).has_access())

    def test_geo_edrpou_match(self):
        """idObjType == 5: перевірка за Geo.GeoDetails"""
        self._create_cert_owner(edrpou='12345678')
        hit = {
            'Document': {'idObjType': 5},
            'Geo': {
                'GeoDetails': {
                    'ApplicantDetails': {
                        'Applicant': [
                            {
                                'ApplicantAddressBook': {
                                    'FormattedNameAddress': {
                                        'Name': {
                                            'FreeFormatName': {'EDRPOU': '12345678'}
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit).has_access())

    def test_design_edrpou_match(self):
        """idObjType == 6: перевірка за Design.DesignDetails (Name та Address)"""
        self._create_cert_owner(edrpou='12345678')

        # Applicant - Address.FormattedAddress.EDRPOU
        hit_applicant_addr = {
            'Document': {'idObjType': 6},
            'Design': {
                'DesignDetails': {
                    'ApplicantDetails': {
                        'Applicant': [
                            {
                                'ApplicantAddressBook': {
                                    'FormattedNameAddress': {
                                        'Address': {
                                            'FormattedAddress': {'EDRPOU': '12345678'}
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit_applicant_addr).has_access())

        # Holder - Address.FormattedAddress.EDRPOU
        hit_holder_addr = {
            'Document': {'idObjType': 6},
            'Design': {
                'DesignDetails': {
                    'HolderDetails': {
                        'Holder': [
                            {
                                'HolderAddressBook': {
                                    'FormattedNameAddress': {
                                        'Address': {
                                            'FormattedAddress': {'EDRPOU': '12345678'}
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit_holder_addr).has_access())

    def test_copyright_edrpou_match(self):
        """idObjType in (10, 13): Авторське право"""
        self._create_cert_owner(edrpou='12345678')
        for details_key, entity_key, book_key in (
            ('ApplicantDetails', 'Applicant', 'ApplicantAddressBook'),
            ('EmployerDetails', 'Employer', 'EmployerAddressBook'),
            ('AuthorDetails', 'Author', 'AuthorAddressBook'),
            ('RepresentativeDetails', 'Representative', 'RepresentativeAddressBook'),
            ('HolderDetails', 'Holder', 'HolderAddressBook'),
        ):
            hit = {
                'Document': {'idObjType': 10},
                'Certificate': {
                    'CopyrightDetails': {
                        details_key: {
                            entity_key: [
                                {
                                    book_key: {
                                        'FormattedNameAddress': {
                                            'Name': {
                                                'FreeFormatName': {'EDRPOU': '12345678'}
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
            self.assertTrue(
                UserDocAccessService(self.user, hit).has_access(),
                f"Failed for entity: {details_key}"
            )

    def test_copyright_agreement_edrpou_match(self):
        """idObjType in (11, 12): Договори (авторське право)"""
        self._create_cert_owner(edrpou='12345678')
        for details_key, entity_key, book_key in (
            ('ApplicantDetails', 'Applicant', 'ApplicantAddressBook'),
            ('LicensorDetails', 'Licensor', 'LicensorAddressBook'),
            ('LicenseeDetails', 'Licensee', 'LicenseeAddressBook'),
            ('AuthorDetails', 'Author', 'AuthorAddressBook'),
        ):
            hit = {
                'Document': {'idObjType': 11},
                'Decision': {
                    'DecisionDetails': {
                        details_key: {
                            entity_key: [
                                {
                                    book_key: {
                                        'FormattedNameAddress': {
                                            'Name': {
                                                'FreeFormatName': {'EDRPOU': '12345678'}
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                }
            }
            self.assertTrue(
                UserDocAccessService(self.user, hit).has_access(),
                f"Failed for agreement entity: {details_key}"
            )

    def test_entity_as_dict_not_list(self):
        """Сутність передана як окремий dict, а не список list"""
        self._create_cert_owner(edrpou='12345678')
        hit = {
            'Document': {'idObjType': 4},
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicantDetails': {
                        'Applicant': {  # Окремий словник
                            'ApplicantAddressBook': {
                                'FormattedNameAddress': {
                                    'Name': {
                                        'FreeFormatName': {'EDRPOU': '12345678'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit).has_access())

    def test_edrpou_numeric_match_with_leading_zeros(self):
        """Збіг чисел з провідними нулями: '01234567' == '1234567'"""
        self._create_cert_owner(edrpou='01234567')
        hit = {
            'Document': {'idObjType': 1},
            'Patent': {
                'I_71': [{'I_71.N': 'ТОВ', 'EDRPOU': '1234567'}]
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit).has_access())

    def test_name_fallback_match(self):
        """ЄДРПОУ не збігся (або відсутній), але збіглося ПІБ заявника"""
        self._create_cert_owner(full_name='Петренко Петро Петрович', edrpou='99999999')
        hit = {
            'Document': {'idObjType': 4},
            'search_data': {
                'applicant': [{'name': 'ПЕТРЕНКО ПЕТРО ПЕТРОВИЧ [UA]'}]
            },
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicantDetails': {
                        'Applicant': [{'ApplicantAddressBook': {'FormattedNameAddress': {'Name': {'FreeFormatName': {'EDRPOU': '00000000'}}}}}]
                    }
                }
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit).has_access())

    def test_no_match_returns_false(self):
        """Ані ЄДРПОУ, ані ім'я не збігаються -> доступ закрито"""
        self._create_cert_owner(full_name='Сидоренко Сидір Сидорович', edrpou='11111111')
        hit = {
            'Document': {'idObjType': 4},
            'search_data': {
                'applicant': [{'name': 'ПЕТРЕНКО ПЕТРО ПЕТРОВИЧ [UA]'}]
            },
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicantDetails': {
                        'Applicant': [{'ApplicantAddressBook': {'FormattedNameAddress': {'Name': {'FreeFormatName': {'EDRPOU': '22222222'}}}}}]
                    }
                }
            }
        }
        self.assertFalse(UserDocAccessService(self.user, hit).has_access())

    def test_multiple_applicants_and_holders_edrpou_match(self):
        """Кілька заявників та власників у списку: збігається 3-й елемент"""
        self._create_cert_owner(edrpou='33333333')
        hit = {
            'Document': {'idObjType': 4},
            'TradeMark': {
                'TrademarkDetails': {
                    'ApplicantDetails': {
                        'Applicant': [
                            {'ApplicantAddressBook': {'FormattedNameAddress': {'Name': {'FreeFormatName': {'EDRPOU': '11111111'}}}}},
                            {'ApplicantAddressBook': {'FormattedNameAddress': {'Name': {'FreeFormatName': {'EDRPOU': '22222222'}}}}},
                            {'ApplicantAddressBook': {'FormattedNameAddress': {'Name': {'FreeFormatName': {'EDRPOU': '33333333'}}}}},
                        ]
                    }
                }
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit).has_access())

    def test_name_normalization_homoglyphs_apostrophes_and_spaces(self):
        """Нормалізація ПІБ та назв: латинські гомогліфи, апострофи, лапки, тире та спецсимволи"""
        # У сертифікаті: кирилиця, апостроф ʼ (U+02BC), дефіс
        self._create_cert_owner(full_name='Квітка-Основʼяненко Іван Олександрович', edrpou='99999999')
        # У заявці: латинські I, a, O, C, пропущений апостроф, довге тире з пробілами, м'який перенос \xad та подвійні пробіли
        hit = {
            'Document': {'idObjType': 1},
            'Claim': {
                'I_98': 'Квітка — Основ\xadяненко  Iван   Oлекcандрович, м. Київ'
            }
        }
        self.assertTrue(UserDocAccessService(self.user, hit).has_access())



