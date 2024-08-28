from collections import defaultdict

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from apps.wkm.models import WKMMark


def wkm_to_dict(record: 'WKMMark') -> dict:
    """Повертає представлення моделі у вигляді словника."""
    res = {
        'PublicationDetails': [
            {
                'PublicationDate': record.bulletin.bulletin_date.strftime('%Y-%m-%d'),
                'PublicationIdentifier': record.bulletin.bull_str,
            }
        ],
        'DecisionDate': record.decision_date.strftime('%Y-%m-%d') if record.decision_date else None,
        'OrderDate': record.order_date.strftime('%Y-%m-%d') if record.order_date else None,
        'RightsDate': record.rights_date.strftime('%Y-%m-%d') if record.rights_date else None,
        'CourtComments': {
            'CourtCommentsUA': record.court_comments_ua,
            'CourtCommentsEN': record.court_comments_eng,
            'CourtCommentsRU': record.court_comments_rus,
        },
        'WordMarkSpecification': {
            'MarkSignificantVerbalElement': [
                {
                    '#text': record.keywords,
                    '@sequenceNumber': 1
                }
            ]
        },
        'HolderDetails': {
            'Holder': []
        }
    }
    for i, owner in enumerate(record.owners.order_by('pk').all(), 1):
        res['HolderDetails']['Holder'].append(
            {
                'HolderAddressBook': {
                    'FormattedNameAddress': {
                        'Name': {
                            'FreeFormatName': {
                                'FreeFormatNameDetails': {
                                    'FreeFormatNameLine': owner.owner_name
                                }
                            }
                        }
                    }
                },
                'HolderSequenceNumber': i
            }
        )

    classes = defaultdict(list)
    for klass in record.wkmclass_set.order_by('class_number', 'ord_num').all():
        classes[klass.class_number].append({
            'ClassificationTermLanguageCode': 'UA',
            'ClassificationTermText': klass.products
        })

    res['GoodsServicesDetails'] = {
        'GoodsServices': {
            'ClassDescriptionDetails': {
                'ClassDescription': []
            }
        }
    }
    for klass in classes:
        res['GoodsServicesDetails']['GoodsServices']['ClassDescriptionDetails']['ClassDescription'].append(
            {
                'ClassNumber': klass,
                'ClassificationTermDetails': {
                    'ClassificationTerm': classes[klass]
                }
            }
        )

    return res
