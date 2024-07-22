from unittest import TestCase

from apps.search.mixins import BiblioDataInvUMLDRawGetMixin, BiblioDataCRRawGetMixin


class BiblioDataInvUMLDRawGetMixinTestCase(TestCase):

    def test_get_biblio_data(self):
        app_data = {
            'Patent': {
                'Test': 'Data'
            }
        }
        mixin = BiblioDataInvUMLDRawGetMixin()
        self.assertEqual(mixin.get_biblio_data(app_data), {'Test': 'Data'})
        app_data = {
            'Claim': {
                'Test': 'Data'
            }
        }
        self.assertEqual(mixin.get_biblio_data(app_data), {'Test': 'Data'})


class BiblioDataCRRawGetMixinTestCase(TestCase):

    def test_get_biblio_data(self):
        app_data = {
            'Certificate': {
                'CopyrightDetails': {
                    'Test': 'Data'
                }
            }
        }
        mixin = BiblioDataCRRawGetMixin()
        self.assertEqual(mixin.get_biblio_data(app_data), {'Test': 'Data'})
        app_data = {
            'Decision': {
                'DecisionDetails': {
                    'Test': 'Data'
                }
            }
        }
        self.assertEqual(mixin.get_biblio_data(app_data), {'Test': 'Data'})
