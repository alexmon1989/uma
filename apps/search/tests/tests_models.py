from django.test import TestCase
from django.conf import settings

from apps.search.models import IpcAppList, WKMMark, WKMMarkOwner, WKMRefOwner, WKMRefBulletin, WKMClass


class TestIpcAppListTestCase(TestCase):

    def test_real_files_path_property(self):
        """Тестирует property real_files_path."""
        app = IpcAppList()
        app.files_path = '\\\\bear\\share\\INVENTIONS\\2023\\a202303880\\'
        self.assertEqual(
            app.real_files_path,
            f'{settings.DOCUMENTS_MOUNT_FOLDER}INVENTIONS/2023/a202303880/'
        )
        app.files_path = 'e:\\poznach_test_sis\\bear_tmpp_sis\\TRADEMARKS\\2023\\m202303880\\'
        self.assertEqual(
            app.real_files_path,
            f'{settings.DOCUMENTS_MOUNT_FOLDER}TRADEMARKS/2023/m202303880/'
        )


class WKMMarkTestCase(TestCase):

    def test_to_dict(self):
        mark_data = {
            'decision_date': '2023-12-12 12:00:00',
            'order_date': '2023-12-12 13:00:00',
            'order_number': '123',
            'rights_date': '2023-12-12 14:00:00',
            'keywords': 'Keywords',
            'state_id': 1,
            'bulletin': WKMRefBulletin.objects.create(
                bulletin_date='2023-12-12 15:00:00',
                bulletin_number=5,
                bull_str='5/2023',
            ),
            'where_to_publish': 'both',
            'court_comments_ua': 'Рішення',
            'court_comments_rus': 'Решение',
            'court_comments_eng': 'Decision',
        }
        mark = WKMMark(**mark_data)
        mark.save()

        owners_names = ['John Smith', 'Bob Jackson']
        for i, n in enumerate(owners_names, 1):
            item = WKMMarkOwner(
                mark=mark,
                owner=WKMRefOwner.objects.create(
                    owner_name=n,
                    country_code='UA',
                ),
                ord_num=i
            )
            item.save()

        WKMClass.objects.create(
            mark=mark,
            class_number=1,
            ord_num=1,
            products='Products list 1'
        )
        WKMClass.objects.create(
            mark=mark,
            class_number=1,
            ord_num=1,
            products='Products list 2'
        )
        WKMClass.objects.create(
            mark=mark,
            class_number=3,
            ord_num=1,
            products='Products list 3'
        )

        expected = {
            'PublicationDetails': [
                {
                    'PublicationDate': '2023-12-12',
                    'PublicationIdentifier': '5/2023',
                }
            ],
            'DecisionDate': '2023-12-12',
            'OrderDate': '2023-12-12',
            'RightsDate': '2023-12-12',
            'HolderDetails': {
                'Holder': [
                    {
                        'HolderAddressBook': {
                           'FormattedNameAddress': {
                               'Name': {
                                   'FreeFormatName': {
                                       'FreeFormatNameDetails': {
                                           'FreeFormatNameLine': 'John Smith'
                                       }
                                   }
                               }
                           }
                        },
                        'HolderSequenceNumber': 1
                    },
                    {
                        'HolderAddressBook': {
                           'FormattedNameAddress': {
                               'Name': {
                                   'FreeFormatName': {
                                       'FreeFormatNameDetails': {
                                           'FreeFormatNameLine': 'Bob Jackson'
                                       }
                                   }
                               }
                           }
                        },
                        'HolderSequenceNumber': 2
                    },
                ]
            },
            'WordMarkSpecification': {
                'MarkSignificantVerbalElement': [
                    {
                        '#text': 'Keywords',
                        '@sequenceNumber': 1
                    }
                ]
            },
            'GoodsServicesDetails': {
                'GoodsServices': {
                    'ClassDescriptionDetails': {
                        'ClassDescription': [
                            {
                                'ClassNumber': 1,
                                'ClassificationTermDetails': {
                                    'ClassificationTerm': [
                                        {
                                            'ClassificationTermLanguageCode': 'UA',
                                            'ClassificationTermText': 'Products list 1'
                                        },
                                        {
                                            'ClassificationTermLanguageCode': 'UA',
                                            'ClassificationTermText': 'Products list 2'
                                        },
                                    ]
                                }
                            },
                            {
                                'ClassNumber': 3,
                                'ClassificationTermDetails': {
                                    'ClassificationTerm': [
                                        {
                                            'ClassificationTermLanguageCode': 'UA',
                                            'ClassificationTermText': 'Products list 3'
                                        }
                                    ]
                                }
                            },
                        ]
                    }
                }
            },
            'CourtComments': {
                'CourtCommentsUA': 'Рішення',
                'CourtCommentsEN': 'Decision',
                'CourtCommentsRU': 'Решение',
            }
        }

        res = mark.to_dict()
        self.assertEqual(res['PublicationDetails'], expected['PublicationDetails'])
        self.assertEqual(res['DecisionDate'], expected['DecisionDate'])
        self.assertEqual(res['OrderDate'], expected['OrderDate'])
        self.assertEqual(res['RightsDate'], expected['RightsDate'])
        self.assertEqual(res['HolderDetails'], expected['HolderDetails'])
        self.assertEqual(res['WordMarkSpecification'], expected['WordMarkSpecification'])
        self.assertEqual(res['CourtComments'], expected['CourtComments'])
        self.assertEqual(res['GoodsServicesDetails'], expected['GoodsServicesDetails'])
