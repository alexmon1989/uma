from django.test import TestCase

from rest_framework import exceptions

from apps.api.services import services

from datetime import datetime
import json


class ApiServicesTestCase(TestCase):

    def test_opendata_prepare_filters(self):
        """Тестирует функцию opendata_prepare_filters (подготовка фильтров)."""
        filters = (
            'obj_state',
            'obj_type',
            'app_date_from',
            'app_date_to',
            'reg_date_from',
            'reg_date_to',
            'last_update_from',
            'last_update_to',
            'app_number',
        )
        input_data = {}
        output_data = services.opendata_prepare_filters(input_data)
        # Если значение фильтра отсутствует во вх. данных, то его и не должно быть в исходящих
        for key in filters:
            self.assertNotIn(key, output_data)

        # Целочисленные фильтры
        filters = (
            'obj_state',
            'obj_type',
        )
        for key in filters:
            input_data = {key: 1}
            output_data = services.opendata_prepare_filters(input_data)
            self.assertEqual(output_data[key], 1)

            input_data = {key: '1'}
            output_data = services.opendata_prepare_filters(input_data)
            self.assertEqual(output_data[key], 1)

            input_data = {key: 'qwe'}
            with self.assertRaisesRegex(exceptions.ParseError, f'Невірне значення параметру {key}'):
                services.opendata_prepare_filters(input_data)

        # Фильтры даты
        filters = (
            'app_date_from',
            'app_date_to',
            'reg_date_from',
            'reg_date_to',
            'last_update_from',
            'last_update_to',
        )
        d = datetime.strptime('21.03.2023', '%d.%m.%Y')
        for key in filters:
            input_data = {key: '21.03.2023'}
            output_data = services.opendata_prepare_filters(input_data)
            self.assertEqual(output_data[key], d)

            input_data = {key: '21/03/2023'}
            with self.assertRaisesRegex(exceptions.ParseError, f'Невірне значення параметру {key}'):
                services.opendata_prepare_filters(input_data)

            input_data = {key: 'abcde'}
            with self.assertRaisesRegex(exceptions.ParseError, f'Невірне значення параметру {key}'):
                services.opendata_prepare_filters(input_data)

            input_data = {key: 123}
            with self.assertRaisesRegex(exceptions.ParseError, f'Невірне значення параметру {key}'):
                services.opendata_prepare_filters(input_data)

        input_data = {'app_number': 'm202300001'}
        output_data = services.opendata_prepare_filters(input_data)
        self.assertEqual(output_data['app_number'], 'm202300001')


class BiblioDataFullPresenterTMTestCase(TestCase):
    biblio_data_presenter: services.BiblioDataFullPresenter = services.BiblioDataFullPresenter()

    def _get_prepared_data(self, source_data: dict) -> dict:
        json_data = json.dumps(source_data)
        instance = {
            'obj_type_id': 4,
            'data': json_data
        }
        self.biblio_data_presenter.set_application_data(instance)
        data = self.biblio_data_presenter.get_prepared_biblio()
        return data

    def test_check_441(self):
        source_data = {
            'Code_441_BulNumber': '37'
        }
        prepared_data = self._get_prepared_data(source_data)
        self.assertEqual(prepared_data['Code_441_BulNumber'], '37')

        source_data = {
            'Code_441_BulNumber': 37
        }
        prepared_data = self._get_prepared_data(source_data)
        self.assertEqual(prepared_data['Code_441_BulNumber'], '37')

    def test_check_ApplicantSequenceNumber(self):
        source_data = {
            "ApplicantDetails": {
                "Applicant": [
                    {
                        "ApplicantSequenceNumber": 1
                    },
                    {
                        "ApplicantSequenceNumber": '2'
                    }
                ]
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for applicant in prepared_data['ApplicantDetails']['Applicant']:
            self.assertIs(type(applicant['ApplicantSequenceNumber']), int)

    def test_check_HolderSequenceNumber(self):
        source_data = {
            "HolderDetails": {
                "Holder": [
                    {
                        "HolderSequenceNumber": 1
                    },
                    {
                        "HolderSequenceNumber": '2'
                    }
                ]
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for holder in prepared_data['HolderDetails']['Holder']:
            self.assertIs(type(holder['HolderSequenceNumber']), int)

    def test_check_MarkImageColourClaimedTextSequenceNumber(self):
        source_data = {
            "WordMarkSpecification": {
                "MarkSignificantVerbalElement": [
                    {
                        "@sequenceNumber": "1"
                    },
                    {
                        "@sequenceNumber": 2
                    }
                ]
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for item in prepared_data['WordMarkSpecification']['MarkSignificantVerbalElement']:
            self.assertIs(type(item['@sequenceNumber']), int)

    def test_check_MarkImageDetailsSequenceNumber(self):
        source_data = {
            "MarkImageDetails": {
                "MarkImage": {
                    "MarkImageColourClaimedText": [
                        {
                            "@sequenceNumber": "1"
                        },
                        {
                            "@sequenceNumber": 2
                        }
                    ]
                }
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for item in prepared_data['MarkImageDetails']['MarkImage']['MarkImageColourClaimedText']:
            self.assertIs(type(item['@sequenceNumber']), int)

    def test_check_GoodsServicesDetailsClassNumber(self):
        source_data = {
            "GoodsServicesDetails": {
                "GoodsServices": {
                    "ClassDescriptionDetails": {
                        "ClassDescription": [
                            {
                                "ClassNumber": "44"
                            },
                            {
                                "ClassNumber": 45
                            }
                        ]
                    }
                }
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for item in prepared_data['GoodsServicesDetails']['GoodsServices']['ClassDescriptionDetails']['ClassDescription']:
            self.assertIs(type(item['ClassNumber']), int)

    def test_check_MarkImageRenditionRepresentationSize(self):
        source_data = {
            "MarkImageDetails": {
                "MarkImage": {
                    "MarkImageRepresentationSize": [
                        {
                            "MarkImageRenditionRepresentationSize": {
                                "Height": 423,
                                "Width": 1400,
                            }
                        }
                    ]
                }
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for item in prepared_data['MarkImageDetails']['MarkImage']['MarkImageRepresentationSize']:
            self.assertIs(type(item['MarkImageRenditionRepresentationSize']['Height']), int)
            self.assertIs(type(item['MarkImageRenditionRepresentationSize']['Width']), int)

        source_data = {
            "MarkImageDetails": {
                "MarkImage": {
                    "MarkImageRepresentationSize": [
                        {
                            "MarkImageRenditionRepresentationSize": {
                                "Height": '423',
                                "Width": '1400',
                            }
                        }
                    ]
                }
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for item in prepared_data['MarkImageDetails']['MarkImage']['MarkImageRepresentationSize']:
            self.assertIs(type(item['MarkImageRenditionRepresentationSize']['Height']), int)
            self.assertIs(type(item['MarkImageRenditionRepresentationSize']['Width']), int)

        source_data = {
            "MarkImageDetails": {
                "MarkImage": {
                    "MarkImageRepresentationSize": [
                        {
                            "MarkImageRenditionRepresentationSize": {
                                "Height": '',
                                "Width": '',
                            }
                        }
                    ]
                }
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for item in prepared_data['MarkImageDetails']['MarkImage']['MarkImageRepresentationSize']:
            self.assertIs(type(item['MarkImageRenditionRepresentationSize']['Height']), int)
            self.assertIs(type(item['MarkImageRenditionRepresentationSize']['Width']), int)

    def test_check_PriorityPartialIndicator(self):
        source_data = {
            "PriorityDetails": {
                "Priority": [
                    {
                        "PriorityPartialIndicator": 'true'
                    },
                    {
                        "PriorityPartialIndicator": 'false'
                    },
                    {
                        "PriorityPartialIndicator": True
                    },
                    {
                        "PriorityPartialIndicator": False
                    }
                ]
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for item in prepared_data['PriorityDetails']['Priority']:
            self.assertIs(type(item['PriorityPartialIndicator']), bool)

    def test_check_ExhibitionPartialIndicator(self):
        source_data = {
            "ExhibitionPriorityDetails": {
                "ExhibitionPriority": [
                    {
                        "ExhibitionPartialIndicator": 'true'
                    },
                    {
                        "ExhibitionPartialIndicator": 'false'
                    },
                    {
                        "ExhibitionPartialIndicator": True
                    },
                    {
                        "ExhibitionPartialIndicator": False
                    }
                ]
            }
        }
        prepared_data = self._get_prepared_data(source_data)
        for item in prepared_data['ExhibitionPriorityDetails']['ExhibitionPriority']:
            self.assertIs(type(item['ExhibitionPartialIndicator']), bool)
