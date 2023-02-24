from django.test import TestCase
from apps.search.services.reports import ReportItemDocxTM, ReportWriterDocx
from apps.search.dataclasses import InidCode

from docx import Document

from pathlib import Path
import tempfile


class ReportItemDocxTmTestCase(TestCase):
    def setUp(self) -> None:
        self.document = Document()

    def test_inid_111(self):
        """Тестирует корректность добавления информации о номере регистрации."""
        # Номер регистрации есть в данных и разрешён для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationNumber': '111111'
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '111', 'Номер свідоцтва', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertTrue('(111)\tНомер свідоцтва: 111111' in p.text)

        # Номер регистрации есть в данных и не разрешён для отображения
        inid_data = [
            InidCode(4, '111', 'Номер свідоцтва', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertFalse('(111)\tНомер свідоцтва: 111111' in p.text)

        # Номера регистрации нет данных, разрешён для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '111', 'Номер свідоцтва', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertFalse('(111)\tНомер свідоцтва: 111111' in p.text)

        # Номер регистрации есть в данных, ИНИД-кода нет в данных для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationNumber': '111111'
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertFalse('(111)\tНомер свідоцтва: 111111' in p.text)

    def test_inid_540(self):
        """
        Тестирует добавление изображения.
        TODO: написать тест
        """
        pass

    def test_inid_141(self):
        """Тестирует корректность добавления информации о значении ИНИД
         (141) Дата закінчення строку дії реєстрації знака."""
        # Данные существуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "TerminationDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '141', 'Дата закінчення строку дії реєстрації знака', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn('(141)\tДата закінчення строку дії реєстрації знака: 23.02.2023', p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '141', 'Дата закінчення строку дії реєстрації знака', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(141)\tДата закінчення строку дії реєстрації знака: 23.02.2023', p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '141', 'Дата закінчення строку дії реєстрації знака', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(141)\tДата закінчення строку дії реєстрації знака: 23.02.2023', p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "TerminationDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(141)\tДата закінчення строку дії реєстрації знака: 23.02.2023', p.text)

    def test_inid_151(self):
        """Тестирует корректность добавления информации о значении ИНИД
        (151) Дата реєстрації."""
        # Данные существуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "RegistrationDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '151', 'Дата реєстрації', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn('(151)\tДата реєстрації: 23.02.2023', p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '151', 'Дата реєстрації', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(151)\tДата реєстрації: 23.02.2023', p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '151', 'Дата реєстрації', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(151)\tДата реєстрації: 23.02.2023', p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "RegistrationDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(151)\tДата реєстрації: 23.02.2023', p.text)

    def test_inid_181(self):
        """Тестирует корректность добавления информации о значении ИНИД
        (181) Очікувана дата закінчення строку дії реєстрації."""
        # Данные существуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ExpiryDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '181', 'Очікувана дата закінчення строку дії реєстрації', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn('(181)\tОчікувана дата закінчення строку дії реєстрації: 23.02.2023', p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '181', 'Очікувана дата закінчення строку дії реєстрації', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(181)\tОчікувана дата закінчення строку дії реєстрації: 23.02.2023', p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '181', 'Очікувана дата закінчення строку дії реєстрації', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(181)\tОчікувана дата закінчення строку дії реєстрації: 23.02.2023', p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ExpiryDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(181)\tОчікувана дата закінчення строку дії реєстрації: 23.02.2023', p.text)

    def test_inid_186(self):
        """Тестирует корректность добавления информации о значении ИНИД
        (186) Очікувана дата продовження строку дії реєстрації."""
        # Данные существуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ProlonagationExpiryDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '186', 'Очікувана дата продовження строку дії реєстрації', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn('(186)\tОчікувана дата продовження строку дії реєстрації: 23.02.2023', p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '186', 'Очікувана дата продовження строку дії реєстрації', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(186)\tОчікувана дата продовження строку дії реєстрації: 23.02.2023', p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '186', 'Очікувана дата продовження строку дії реєстрації', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(186)\tОчікувана дата продовження строку дії реєстрації: 23.02.2023', p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ProlonagationExpiryDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(186)\tОчікувана дата продовження строку дії реєстрації: 23.02.2023', p.text)

    def test_inid_210(self):
        """Тестирует корректность добавления информации о значении ИНИД
        (210) Порядковий номер заявки."""
        # Данные существуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ApplicationNumber": "m202200001"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '210', 'Порядковий номер заявки', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn('(210)\tПорядковий номер заявки: m202200001', p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '210', 'Порядковий номер заявки', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(210)\tПорядковий номер заявки: m202200001', p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '210', 'Порядковий номер заявки', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(210)\tПорядковий номер заявки: m202200001', p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ApplicationNumber": "m202200001"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(210)\tПорядковий номер заявки: m202200001', p.text)

    def test_inid_220(self):
        """Тестирует корректность добавления информации о значении ИНИД
        (220) Дата подання заявки."""
        # Данные существуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ApplicationDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '220', 'Дата подання заявки', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn('(220)\tДата подання заявки: 23.02.2023', p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '220', 'Дата подання заявки', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(220)\tДата подання заявки: 23.02.2023', p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '220', 'Дата подання заявки', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(220)\tДата подання заявки: 23.02.2023', p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ApplicationDate": "2023-02-23"
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(220)\tДата подання заявки: 23.02.2023', p.text)

    def test_inid_531(self):
        """Тестирует корректность добавления информации о значении ИНИД
        (531) Віденська класифікація."""
        # Данные существуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "MarkImageDetails": {
                        "MarkImage": {
                            "MarkImageCategory": {
                                "CategoryCodeDetails": {
                                    "CategoryCode": [
                                        "01.01.01",
                                        "02.02.02",
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '531', 'Віденська класифікація', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn('(531)\tВіденська класифікація:\n01.01.01\n02.02.02', p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '531', 'Віденська класифікація', 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(531)\tВіденська класифікація:\n01.01.01\n02.02.02', p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '531', 'Віденська класифікація', 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(531)\tВіденська класифікація:\n01.01.01\n02.02.02', p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "MarkImageDetails": {
                        "MarkImage": {
                            "MarkImageCategory": {
                                "CategoryCodeDetails": {
                                    "CategoryCode": [
                                        "01.01.01",
                                        "02.02.02",
                                    ]
                                }
                            }
                        }
                    }
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn('(531)\tВіденська класифікація:\n01.01.01\n02.02.02', p.text)

    def test_inid_300(self):
        """Тестирует корректность добавления информации о значении ИНИД
        (300) Дані щодо пріоритету відповідно до Паризької конвенції та інші дані,
        пов'язані зі старшинством або реєстрацією знака у країні походження."""
        # Данные существуют и разрешены для отображения
        inid_title = "Дані щодо пріоритету відповідно до Паризької конвенції та інші дані, " \
                     "пов'язані зі старшинством або реєстрацією знака у країні походження"
        expected_str = f"(300)\t{inid_title}:\nm202300001; 2023-02-24; EN\nm202300001; 2023-02-25; US"
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "PriorityDetails": {
                        "Priority": [
                            {
                                "PriorityCountryCode": "EN",
                                "PriorityDate": "2023-02-24",
                                "PriorityNumber": "m202300001"
                            },
                            {
                                "PriorityCountryCode": "US",
                                "PriorityDate": "2023-02-25",
                                "PriorityNumber": "m202300001"
                            },
                        ]
                    }
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '300', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '300', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '300', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "PriorityDetails": {
                        "Priority": [
                            {
                                "PriorityCountryCode": "EN",
                                "PriorityDate": "2023-02-24",
                                "PriorityNumber": "m202300001"
                            },
                            {
                                "PriorityCountryCode": "US",
                                "PriorityDate": "2023-02-25",
                                "PriorityNumber": "m202300001"
                            },
                        ]
                    }
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

    def test_inid_731(self):
        """
        Тестирует корректность добавления информации о значении ИНИД (731) Ім'я та адреса заявника
        TODO: Несколько заявителей
        """
        # Данные существуют и разрешены для отображения (заявка)
        inid_title = "Ім'я та адреса заявника"
        expected_str = f"(731)\t{inid_title}:\nІваненко Іван Іванович"
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ApplicantDetails": {
                        "Applicant": [
                            {
                                "ApplicantAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": "UA",
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLine": "Адреса"
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іваненко Іван Іванович"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            'search_data': {
                'obj_state': 1
            }
        }
        inid_data = [
            InidCode(4, '731', inid_title, 1, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '731', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют и разрешены для отображения (свидетельство)
        expected_str = f"(731)\t{inid_title}:\nІваненко Іван Іванович\nАдреса (UA)"
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ApplicantDetails": {
                        "Applicant": [
                            {
                                "ApplicantAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": "UA",
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLine": "Адреса"
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іваненко Іван Іванович"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '731', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '731', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '731', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "ApplicantDetails": {
                        "Applicant": [
                            {
                                "ApplicantAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": "UA",
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLine": "Адреса"
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іваненко Іван Іванович"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

    def test_inid_732(self):
        """
        Тестирует корректность добавления информации о значении ИНИД (732) Ім'я та адреса володільця реєстрації
        TODO: Несколько владельцев
        """
        # Данные существуют и разрешены для отображения
        inid_title = "Ім'я та адреса володільця реєстрації"
        expected_str = f"(732)\t{inid_title}:\nІваненко Іван Іванович\nАдреса (UA)"
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "HolderDetails": {
                        "Holder": [
                            {
                                "HolderAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": "UA",
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLine": "Адреса",
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іваненко Іван Іванович"
                                                },
                                            }
                                        }
                                    }
                                },
                            }
                        ]
                    },
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '732', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '732', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '732', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '732', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "HolderDetails": {
                        "Holder": [
                            {
                                "HolderAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": "UA",
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLine": "Адреса",
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Іваненко Іван Іванович"
                                                },
                                            }
                                        }
                                    }
                                },
                            }
                        ]
                    },
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

    def test_inid_740(self):
        """
        Тестирует корректность добавления информации о значении ИНИД (740) Ім'я та адреса представника
        """
        # Данные существуют и разрешены для отображения
        inid_title = "Ім'я та адреса представника"
        expected_str = f"(740)\t{inid_title}:\nІваненко Іван Іванович\nАдреса (UA)"
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "RepresentativeDetails": {
                        "Representative": [
                            {
                                "RepresentativeAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": "UA",
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLine": "Адреса"
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameDetails": {
                                                        "FreeFormatNameLine": "Іваненко Іван Іванович"
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
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '740', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '740', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '740', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '740', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "RepresentativeDetails": {
                        "Representative": [
                            {
                                "RepresentativeAddressBook": {
                                    "FormattedNameAddress": {
                                        "Address": {
                                            "AddressCountryCode": "UA",
                                            "FreeFormatAddress": {
                                                "FreeFormatAddressLine": "Адреса"
                                            }
                                        },
                                        "Name": {
                                            "FreeFormatName": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameDetails": {
                                                        "FreeFormatNameLine": "Іваненко Іван Іванович"
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
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

    def test_inid_750(self):
        """
        Тестирует корректность добавления информации о значении ИНИД (750) Адреса для листування
        """
        # Данные существуют и разрешены для отображения
        inid_title = "Ім'я та адреса представника"
        expected_str = f"(750)\t{inid_title}:\nІваненко Іван Іванович\nАдреса (UA)"
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "CorrespondenceAddress": {
                        "CorrespondenceAddressBook": {
                            "Address": {
                                "AddressCountryCode": "UA",
                                "FreeFormatAddressLine": "Адреса"
                            },
                            "Name": {
                                "FreeFormatNameLine": "Іваненко Іван Іванович"
                            }
                        }
                    },
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '750', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '750', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '750', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '750', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "CorrespondenceAddress": {
                        "CorrespondenceAddressBook": {
                            "Address": {
                                "AddressCountryCode": "UA",
                                "FreeFormatAddressLine": "Адреса"
                            },
                            "Name": {
                                "FreeFormatNameLine": "Іваненко Іван Іванович"
                            }
                        }
                    },
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

    def test_inid_591(self):
        """
        Тестирует корректность добавления информации о значении ИНИД (591) Інформація щодо заявлених кольорів
        """
        # Данные существуют и разрешены для отображения
        inid_title = "Інформація щодо заявлених кольорів"
        expected_str = f"(591)\t{inid_title}: чорний, білий"
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "MarkImageDetails": {
                        "MarkImage": {
                            "MarkImageColourClaimedText": [
                                {
                                    "#text": "чорний"
                                },
                                {
                                    "#text": "білий"
                                }
                            ]
                        }
                    }
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '591', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '591', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '591', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '591', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "MarkImageDetails": {
                        "MarkImage": {
                            "MarkImageColourClaimedText": [
                                {
                                    "#text": "чорний"
                                },
                                {
                                    "#text": "білий"
                                }
                            ]
                        }
                    }
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

    def test_inid_511(self):
        """
        Тестирует корректность добавления информации о значении ИНИД (511) Індекси Ніццької класифікації
        """
        # Данные существуют и разрешены для отображения
        inid_title = "Індекси Ніццької класифікації"
        expected_str = f"(511)\t{inid_title}: 1, 2"
        expected_str += f"\nКл. 1:\tзначення 1.1; значення 1.2"
        expected_str += f"\nКл. 2:\tзначення 2.1; значення 2.2"
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "GoodsServicesDetails": {
                        "GoodsServices": {
                            "ClassDescriptionDetails": {
                                "ClassDescription": [
                                    {
                                        "ClassNumber": 1,
                                        "ClassificationTermDetails": {
                                            "ClassificationTerm": [
                                                {
                                                    "ClassificationTermText": "значення 1.1"
                                                },
                                                {
                                                    "ClassificationTermText": "значення 1.2"
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "ClassNumber": 2,
                                        "ClassificationTermDetails": {
                                            "ClassificationTerm": [
                                                {
                                                    "ClassificationTermText": "значення 2.1"
                                                },
                                                {
                                                    "ClassificationTermText": "значення 2.2"
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    },
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '511', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '511', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют и запрещены для отображения
        inid_data = [
            InidCode(4, '511', inid_title, 2, False)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные отсутствуют и разрешены для отображения
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {}
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '511', inid_title, 2, True)
        ]
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)

        # Данные существуют, ИНИД код - нет
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    "GoodsServicesDetails": {
                        "GoodsServices": {
                            "ClassDescriptionDetails": {
                                "ClassDescription": [
                                    {
                                        "ClassNumber": 1,
                                        "ClassificationTermDetails": {
                                            "ClassificationTerm": [
                                                {
                                                    "ClassificationTermText": "значення 1.1"
                                                },
                                                {
                                                    "ClassificationTermText": "значення 1.2"
                                                }
                                            ]
                                        }
                                    },
                                    {
                                        "ClassNumber": 2,
                                        "ClassificationTermDetails": {
                                            "ClassificationTerm": [
                                                {
                                                    "ClassificationTermText": "значення 2.1"
                                                },
                                                {
                                                    "ClassificationTermText": "значення 2.2"
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    },
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = []
        item = ReportItemDocxTM(biblio_data, inid_data)
        p = item.write(self.document)
        self.assertNotIn(expected_str, p.text)


class ReportWriterDocxTestCase(TestCase):
    """Тестирует класс создания файла отчёта в формате .docx."""
    report_path = Path(tempfile.gettempdir()) / 'report.docx'
    # report_path = Path('report.docx')

    def test_generates_report(self):
        """Тестирует создание отчёта."""
        biblio_data = {
            'TradeMark': {
                'TrademarkDetails': {
                    'RegistrationNumber': '111111'
                }
            },
            'search_data': {
                'obj_state': 2
            }
        }
        inid_data = [
            InidCode(4, '111', 'Номер свідоцтва', 2, True)
        ]
        items = [ReportItemDocxTM(biblio_data, inid_data)]

        file_path = Path(tempfile.gettempdir()) / 'report.docx'
        writer = ReportWriterDocx(items)
        writer.generate(file_path)
        self.assertTrue(file_path.exists())

# class InidCodesServiceTestCase(TestCase):
