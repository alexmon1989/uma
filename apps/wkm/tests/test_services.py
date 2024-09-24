from django.test import TestCase
from apps.wkm.models import WKMMark, WKMRefBulletin, WKMMarkOwner, WKMRefOwner, WKMClass, WKMVienna, WKMDocument, WKMDocumentType
from apps.wkm.services import WKMJSONConverter


class WKMMarkConverterTest(TestCase):

    databases = ("default", "WellKnownMarks", )

    def setUp(self):
        # Створення необхідних об'єктів для тестів
        self.bulletin = WKMRefBulletin.objects.create(
            bulletin_date='2023-01-01',
            bulletin_number='202301',
            bull_str='2023/01'
        )
        self.owner1 = WKMRefOwner.objects.create(owner_name='Owner 1', country_code='UA')
        self.owner2 = WKMRefOwner.objects.create(owner_name='Owner 2', country_code='US')
        self.mark = WKMMark.objects.create(
            decision_date='2023-01-10',
            order_date='2023-01-15',
            order_number='test_order_num',
            rights_date='2023-01-20',
            keywords='Test Keyword',
            mark_image=b'test_image_data',
            bulletin=self.bulletin,
            court_comments_ua='UA Comment',
            court_comments_eng='ENG Comment'
        )
        WKMDocument.objects.create(
            wkm=self.mark,
            document_type=WKMDocumentType.objects.create(code='decision', value='Рішення')
        )
        WKMDocument.objects.create(
            wkm=self.mark,
            document_type=WKMDocumentType.objects.create(code='nakaz_dsiv', value='Наказ ДСІВ')
        )
        self.mark.refresh_from_db()

        WKMMarkOwner.objects.create(mark=self.mark, owner=self.owner1, ord_num=1)
        WKMMarkOwner.objects.create(mark=self.mark, owner=self.owner2, ord_num=2)

        WKMClass.objects.create(mark=self.mark, class_number=1, ord_num=1, products='Product 1')
        WKMClass.objects.create(mark=self.mark, class_number=2, ord_num=2, products='Product 2')
        WKMVienna.objects.create(mark=self.mark, class_number='ViennaClass1')
        WKMVienna.objects.create(mark=self.mark, class_number='ViennaClass2')

    def test_add_publication_details(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        self.assertEqual(result['PublicationDetails'][0]['PublicationDate'], '2023-01-01')
        self.assertEqual(result['PublicationDetails'][0]['PublicationIdentifier'], '2023/01')

    def test_add_court_comments(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        self.assertEqual(result['CourtComments']['CourtCommentsUA'], 'UA Comment')
        self.assertEqual(result['CourtComments']['CourtCommentsEN'], 'ENG Comment')
        self.assertNotIn('CourtCommentsRU', result['CourtComments'])  # Тест на відсутність даних

    def test_add_mark_image_details(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        self.assertEqual(result['MarkImageDetails']['MarkImage']['MarkImageFileFormat'], 'JPG')
        self.assertEqual(result['MarkImageDetails']['MarkImage']['MarkImageFilename'], f"{self.mark.id}.jpg")

    def test_add_vienna_classes(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        vienna_classes = result['MarkImageDetails']['MarkImage']['MarkImageCategory']['CategoryCodeDetails'][
            'CategoryCode']
        self.assertIn('ViennaClass1', vienna_classes)
        self.assertIn('ViennaClass2', vienna_classes)

    def test_add_holders(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        self.assertEqual(len(result['HolderDetails']['Holder']), 2)
        self.assertEqual(result['HolderDetails']['Holder'][0]['HolderSequenceNumber'], 1)
        self.assertEqual(result['HolderDetails']['Holder'][0]['HolderAddressBook']['FormattedNameAddress'][
                             'Name']['FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLine'], 'Owner 1')
        self.assertEqual(result['HolderDetails']['Holder'][0]['HolderAddressBook']['FormattedNameAddress'][
                             'Address']['AddressCountryCode'], 'UA')
        self.assertEqual(result['HolderDetails']['Holder'][1]['HolderSequenceNumber'], 2)
        self.assertEqual(result['HolderDetails']['Holder'][1]['HolderAddressBook']['FormattedNameAddress'][
                             'Name']['FreeFormatName']['FreeFormatNameDetails']['FreeFormatNameLine'], 'Owner 2')
        self.assertEqual(result['HolderDetails']['Holder'][1]['HolderAddressBook']['FormattedNameAddress'][
                             'Address']['AddressCountryCode'], 'US')

    def test_add_nice_classes(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        nice_classes = result['GoodsServicesDetails']['GoodsServices']['ClassDescriptionDetails'][
            'ClassDescription']
        self.assertEqual(len(nice_classes), 2)
        self.assertEqual(nice_classes[0]['ClassNumber'], 1)
        self.assertEqual(nice_classes[1]['ClassNumber'], 2)

    def test_add_word_mark_specification(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        expected = {
            'WordMarkSpecification': {
                'MarkSignificantVerbalElement': [{
                    '#text': 'Test Keyword',
                    '@sequenceNumber': 1
                }]
            }
        }
        self.assertIn('WordMarkSpecification', result)
        self.assertEqual(expected['WordMarkSpecification'], result['WordMarkSpecification'])

    def test_add_decision_details(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        expected = {
            'DecisionDetails': {
                'DecisionDate': '2023-01-10',
                'DecisionFile': {
                    'DecisionFilename': 'decision.pdf'
                }
            }
        }
        self.assertIn('DecisionDetails', result)
        self.assertEqual(expected['DecisionDetails'], result['DecisionDetails'])

    def test_add_order_details(self):
        converter = WKMJSONConverter(self.mark)
        result = converter.convert()

        expected = {
            'OrderDetails': {
                'OrderDate': '2023-01-15',
                'OrderNumber': 'test_order_num',
                'OrderFile': {
                    'OrderFilename': 'nakaz_dsiv.pdf',
                    'OrderType': 'Наказ ДСІВ'
                }
            }
        }
        self.assertIn('OrderDetails', result)
        self.assertEqual(expected['OrderDetails'], result['OrderDetails'])
