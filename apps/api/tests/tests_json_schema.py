from django.test import TestCase
from django.conf import settings

from jsonschema import validate, Draft202012Validator, ValidationError

import json
import os


class TMJsonSchemaTestCase(TestCase):
    schema: dict = {}

    def setUp(self) -> None:
        with open(os.path.join(settings.BASE_DIR, 'apps', 'api', 'json_schema', 'tm.json')) as f:
            self.schema = json.load(f)

    def testLastUpdate(self) -> None:
        instance = {"last_update": "2001-10-23T15:32:12.9023368Z"}
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

        instance = {"last_update": "2001-10-23T15:32:12"}
        with self.assertRaises(ValidationError):
            validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testApplicantDetails(self) -> None:
        instance = {
            "data": {
                "ApplicantDetails": {
                    "Applicant": [
                        {
                            "ApplicantAddressBook": {
                                "FormattedNameAddress": {
                                    "Address": {
                                        "AddressCountryCode": "NL",
                                        "FreeFormatAddress": {
                                            "FreeFormatAddressLine": "Веєна 455, 3013 АЛ Роттердам Нідерланди (Weena 455, 3013 AL Rotterdam, The Netherlands)"
                                        }
                                    },
                                    "Name": {
                                        "FreeFormatName": {
                                            "EDRPOU": "",
                                            "NameKind": "legal_entity",
                                            "FreeFormatNameDetails": {
                                                "FreeFormatNameLine": "Юнілівер АйПі Холдінгз Бі.Ві. (Unilever IP Holdings B.V.)"
                                            }
                                        }
                                    }
                                }
                            },
                            "ApplicantSequenceNumber": 1
                        }
                    ]
                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testApplicationDate(self) -> None:
        instance = {
            "data": {
                "ApplicationDate": "2020-06-09"
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

        instance = {
            "data": {
                "ApplicationDate": "not valid"
            }
        }
        with self.assertRaises(ValidationError):
            validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testApplicationNumber(self) -> None:
        instance = {
            "data": {
                "ApplicationNumber": "m202300001"
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testAssociatedRegistrationApplicationDetails(self) -> None:
        instance = {
            "data": {
                "AssociatedRegistrationApplicationDetails": {
                    "AssociatedRegistrationApplication": {
                        "AssociatedMarkDetails": {
                            "AssociatedMark": [
                                {
                                    "AssociatedApplicationNumber": "№14224",
                                    "AssociatedApplicationDate": "1999-12-29"
                                },
                                {
                                    "AssociatedApplicationNumber": "№14225",
                                    "AssociatedApplicationDate": "1999-12-29"
                                },
                                {
                                    "AssociatedApplicationNumber": "№15129",
                                    "AssociatedApplicationDate": "2000-08-15"
                                },
                                {
                                    "AssociatedApplicationNumber": "№21585",
                                    "AssociatedApplicationDate": "2001-11-15"
                                }
                            ]
                        },
                        "AssociatedRegistrationDetails": {
                            "DivisionalApplication": [
                                {
                                    "AssociatedRegistration": {
                                        "AssociatedRegistrationDate": "2018-10-01",
                                        "AssociatedRegistrationNumber": "1455384"
                                    }
                                }
                            ]
                        },
                        "DivisionalApplicationDetails": {
                            "DivisionalApplication": [
                                {
                                    "InitialApplicationNumber": "m201013771",
                                    "InitialApplicationDate": "2010-09-07"
                                }
                            ]
                        }
                    }
                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testCode_441(self) -> None:
        instance = {
            "data": {
                "Code_441": "2010-09-07"
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

        instance = {
            "data": {
                "Code_441": "not valid"
            }
        }
        with self.assertRaises(ValidationError):
            validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testCode_441_BulNumber(self) -> None:
        instance = {
            "data": {
                "Code_441_BulNumber": "37"
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

        instance = {
            "data": {
                "Code_441_BulNumber": 123
            }
        }
        with self.assertRaises(ValidationError):
            validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testCorrespondenceAddress(self) -> None:
        instance = {
            "data": {
                "CorrespondenceAddress": {
                    "CorrespondenceAddressBook": {
                        "Address": {
                            "AddressCountryCode": "UA",
                            "FreeFormatAddressLine": "а/с 3120, м. Харків, 61072",
                            "AddressPostcode": "61072"
                        },
                        "Name": {
                            "FreeFormatNameLine": "Крахмальова Тетяна Ігорівна"
                        }
                    }

                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testDeclamation(self) -> None:
        instance = {
            "data": {
                "Declamation": "Lorem ipsum"
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testExhibitionPriorityDetails(self) -> None:
        instance = {
            "data": {
                "ExhibitionPriorityDetails": [
                    {
                        "ExhibitionCountryCode": "UA",
                        "ExhibitionDate": "2001-11-14",
                        "ExhibitionPartialIndicator": True,
                        "ExhibitionPartialGoodsServices": {
                            "ClassDescriptionDetails": {
                                "ClassDescription": {
                                    "ClassDescriptionDetails": {
                                        "ClassDescription": [
                                            {
                                                "ClassNumber": 32,
                                                "ClassificationTermDetails": {
                                                    "ClassificationTerm": [
                                                        {
                                                            "ClassificationTermLanguageCode": "uk",
                                                            "ClassificationTermText": "столові води (газовані)"
                                                        },
                                                        {
                                                            "ClassificationTermLanguageCode": "uk",
                                                            "ClassificationTermText": "столові води (негазовані)"
                                                        }
                                                    ]
                                                }
                                            },
                                            {
                                                "ClassNumber": 33,
                                                "ClassificationTermDetails": {
                                                    "ClassificationTerm": [
                                                        {
                                                            "ClassificationTermLanguageCode": "uk",
                                                            "ClassificationTermText": "столові води (газовані)"
                                                        },
                                                        {
                                                            "ClassificationTermLanguageCode": "uk",
                                                            "ClassificationTermText": "столові води (негазовані)"
                                                        }
                                                    ]
                                                }
                                            },
                                        ]
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testGoodsServicesDetails(self) -> None:
        instance = {
            "data": {
                "GoodsServicesDetails": {
                    "GoodsServices": {
                        "ClassDescriptionDetails": {
                            "ClassDescription": [
                                {
                                    "ClassNumber": "41",
                                    "ClassificationTermDetails": {
                                        "ClassificationTerm": [
                                            {
                                                "ClassificationTermLanguageCode": "uk",
                                                "ClassificationTermText": "Академії (освіта)"
                                            },
                                            {
                                                "ClassificationTermLanguageCode": "uk",
                                                "ClassificationTermText": "викладання"
                                            }
                                        ]
                                    }
                                },
                                {
                                    "ClassNumber": "42",
                                    "ClassificationTermDetails": {
                                        "ClassificationTerm": [
                                            {
                                                "ClassificationTermLanguageCode": "uk",
                                                "ClassificationTermText": "Академії (освіта)"
                                            },
                                            {
                                                "ClassificationTermLanguageCode": "uk",
                                                "ClassificationTermText": "викладання"
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }

                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testHolderDetails(self) -> None:
        instance = {
            "data": {
                "HolderDetails": {
                    "Holder": [
                        {
                            "HolderAddressBook": {
                                "FormattedNameAddress": {
                                    "Address": {
                                        "AddressCountryCode": "UA",
                                        "FreeFormatAddress": {
                                            "FreeFormatAddressLine": "вул. Чистяківська, 4, кв. 312, м. Київ, 03062",
                                            "FreeFormatAddressLineOriginal": "",
                                            "FreeFormatNameLine": "Мамулашвілі Ушангі",
                                            "FreeFormatNameLineOriginal": ""
                                        }
                                    },
                                    "Name": {
                                        "FreeFormatName": {
                                            "EDRPOU": "",
                                            "NameKind": "Other",
                                            "FreeFormatNameDetails": {
                                                "FreeFormatNameLine": "Мамулашвілі Ушангі",
                                                "FreeFormatNameLineOriginal": ""
                                            }
                                        }
                                    }
                                }
                            },
                            "HolderSequenceNumber": 1
                        }
                    ]
                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testMarkImageDetails(self) -> None:
        instance = {
            "data": {
                "MarkImageDetails": {
                    "MarkImage": {
                        "MarkImageRepresentationSize": [
                            {
                                "MarkImageRenditionRepresentationSize": {
                                    "Height": 44,
                                    "Unit": "Pixel",
                                    "Width": 395
                                },
                                "MarkImageRenditionColourMode": "BW"
                            }
                        ],
                        "MarkImageColourIndicator": "0",
                        "MarkImageCategory": {
                            "CategoryCodeDetails": {
                                "CategoryCode": [
                                    "28.11.00"
                                ]
                            }
                        },
                        "MarkImageColourClaimedText": [
                            {
                                "@sequenceNumber": "1",
                                "#text": "червоний"
                            },
                            {
                                "@sequenceNumber": "2",
                                "#text": " білий"
                            }
                        ],
                        "MarkImageFileFormat": "JPEG",
                        "MarkImageFilename": "/media/TRADE_MARKS/2021/m202105223/337843.jpeg"
                    }

                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testPriorityDetails(self) -> None:
        instance = {
            "data": {
                "PriorityDetails": {
                    "Priority": [
                        {
                            "PriorityCountryCode": "PL",
                            "PriorityNumber": "Z-343967",
                            "PriorityDate": "23.07.2008",
                            "PriorityPartialIndicator": False
                        }
                    ]
                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

        instance = {
            "data": {
                "PriorityDetails": {
                    "Priority": [
                        {
                            "PriorityNumber": "m 2018 18268",
                            "PriorityDate": "03.08.2018",
                            "PriorityPartialIndicator": "true",
                            "PriorityPartialGoodsServices": {
                                "ClassDescriptionDetails": {
                                    "ClassDescription": {
                                        "ClassDescriptionDetails": {
                                            "ClassDescription": [
                                                {
                                                    "ClassNumber": 5,
                                                    "ClassificationTermDetails": {
                                                        "ClassificationTerm": [
                                                            {
                                                                "ClassificationTermLanguageCode": "uk",
                                                                "ClassificationTermText": "Дієтичні харчові продукти і речовини, призначені для медичного використання"
                                                            },
                                                            {
                                                                "ClassificationTermLanguageCode": "uk",
                                                                "ClassificationTermText": "дієтичні добавки для людей"
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            "PriorityCountryCode": "UA"
                        }
                    ]
                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testPublicationDetails(self) -> None:
        instance = {
            "data": {
                "PublicationDetails": [
                    {
                        "PublicationDate": "2023-09-27",
                        "PublicationIdentifier": "39/2023"
                    }
                ]
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testRepresentativeDetails(self) -> None:
        instance = {
            "data": {
                "RepresentativeDetails": {
                    "Representative": [
                        {
                            "RepresentativeAddressBook": {
                                "FormattedNameAddress": {
                                    "Name": {
                                        "FreeFormatName": {
                                            "FreeFormatNameDetails": {
                                                "FreeFormatNameDetails": {
                                                    "FreeFormatNameLine": "Сердюк Олексій Володимирович"
                                                }
                                            }
                                        }
                                    },
                                    "Address": {
                                        "AddressCountryCode": "UA",
                                        "FreeFormatAddress": {
                                            "FreeFormatAddressLine": "*"
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testUssrApplicationDetails(self) -> None:
        instance = {
            "data": {
                "UssrApplicationDetails": {
                    "UssrApplication": {
                        "UssrApplicationNumber": "93020247",
                        "UssrApplicationDate": "1993-02-04"
                    }
                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testWordMarkSpecification(self) -> None:
        instance = {
            "data": {
                "WordMarkSpecification": {
                    "MarkSignificantVerbalElement": [
                        {
                            "#text": "georgian legion",
                            "@sequenceNumber": "1"
                        },
                        {
                            "#text": "georgian",
                            "@sequenceNumber": "2"
                        },
                        {
                            "#text": "legion",
                            "@sequenceNumber": "3"
                        }
                    ]

                }
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    def testStages(self) -> None:
        instance = {
            "data": {
                "stages": [
                    {
                        "title": "Торговельну марку зареєстровано",
                        "status": "done"
                    },
                    {
                        "title": "Підготовка до державної реєстрації та публікації",
                        "status": "done"
                    },
                    {
                        "title": "Кваліфікаційна експертиза",
                        "status": "done"
                    },
                    {
                        "title": "Формальна експертиза",
                        "status": "done"
                    },
                    {
                        "title": "Встановлення дати подання",
                        "status": "done"
                    },
                    {
                        "title": "Реєстрація первинних документів, попередня експертиза та введення відомостей до бази даних",
                        "status": "done"
                    }
                ]
            }
        }
        validate(instance=instance, schema=self.schema, format_checker=Draft202012Validator.FORMAT_CHECKER)