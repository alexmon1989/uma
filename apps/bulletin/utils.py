from django.urls import reverse
from django.conf import settings
from .models import EBulletinData, ClListOfficialBulletinsIp
import datetime
import os


def prepare_tm_data(record):
    """Подлготавливет данные о ТМ для отображения в бюлетне."""
    hit = record.to_dict()
    data = hit['TradeMark']['TrademarkDetails']
    biblio_data = dict()

    # (210) Номер заявки
    url = reverse("search:detail", args=(record.meta.id,))
    biblio_data['code_210'] = {
        'title': '(210) Номер заявки',
        'value': f"<a href=\"{url}\" target=\"_blank\">{data['ApplicationNumber']}</a>"
    }

    # 220 - Дата подання заявки
    biblio_data['code_220'] = {
        'title': '(220) Дата подання заявки',
        'value': datetime.datetime.strptime(hit['search_data']['app_date'][:10], '%Y-%m-%d').strftime('%d.%m.%Y')
    }

    # 230 - Дата виставкового пріорітету
    biblio_data['code_230'] = {
        'title': '(230) Дата виставкового пріорітету',
        'value': None
    }
    if data.get('ExhibitionPriorityDetails', {}).get('ExhibitionPriority', []):
        dates = []
        for item in data['ExhibitionPriorityDetails']['ExhibitionPriority']:
            dates.append(item.get('ExhibitionDate', ''))
        biblio_data['code_230']['value'] = '; '.join(dates)

    # 310 - номер попередньої заявки відповідно до Паризької конвенції
    biblio_data['code_310'] = {
        'title': '(310) Номер попередньої заявки відповідно до Паризької конвенції',
        'value': None
    }
    if data.get('PriorityDetails', {}).get('Priority', []):
        app_numbers = []
        for item in data['PriorityDetails']['Priority']:
            app_numbers.append(item.get('PriorityNumber', ''))
        biblio_data['code_310']['value'] = '; '.join(app_numbers)

    # 320 - дата подання попередньої заявки відповідно до Паризької конвенції
    biblio_data['code_320'] = {
        'title': '(320) Дата подання попередньої заявки відповідно до Паризької конвенції',
        'value': None
    }
    if data.get('PriorityDetails', {}).get('Priority', []):
        dates = []
        for item in data['PriorityDetails']['Priority']:
            dates.append(item.get('PriorityDate', ''))
        biblio_data['code_320']['value'] = '; '.join(dates)

    # 330 - двобуквенний код держави-учасниці Паризької конвенції
    biblio_data['code_330'] = {
        'title': '(330) Двобуквенний код держави-учасниці Паризької конвенції',
        'value': None
    }
    if data.get('PriorityDetails', {}).get('Priority', []):
        countries = []
        for item in data['PriorityDetails']['Priority']:
            countries.append(item.get('PriorityCountryCode', ''))
        biblio_data['code_330']['value'] = '; '.join(countries)

    # 441 - Дата публікації заявки
    date_441 = EBulletinData.objects.filter(app_number=data['ApplicationNumber']).first().publication_date
    bul_num_441 = ClListOfficialBulletinsIp.objects.get(date_from__lte=date_441, date_to__gte=date_441)
    biblio_data['code_441'] = {
        'title': '(441) Дата публікації відомостей про заявку та номер бюлетня',
        'value': f"{date_441.strftime('%d.%m.%Y')}, бюл. № {bul_num_441.bul_number}"
    }

    # 511 - індекс (індекси) МКТП для реєстрації знаків та перелік товарів і послуг
    biblio_data['code_511'] = {
        'title': '(511) Індекс (індекси) МКТП для реєстрації знаків та перелік товарів і послуг',
        'value': None
    }
    if data.get('GoodsServicesDetails', {}).get('GoodsServices', {}).get('ClassDescriptionDetails', {}).get(
            'ClassDescription'):
        classes = data['GoodsServicesDetails']['GoodsServices']['ClassDescriptionDetails']['ClassDescription']
        res = ''
        for c in classes:
            res += f"<strong>Кл. {c['ClassNumber']}:</strong> "
            terms = []
            if c.get('ClassificationTermDetails'):
                for term in c['ClassificationTermDetails']['ClassificationTerm']:
                    terms.append(term['ClassificationTermText'])
            res += "; ".join(terms)
            res += "<br>"
        biblio_data['code_511']['value'] = res

    # 531 - індекс (індекси) Міжнародної класифікації зображувальних елементів знака
    biblio_data['code_531'] = {
        'title': '(531) Індекс (індекси) Міжнародної класифікації зображувальних елементів знака',
        'value': None
    }
    if data.get('MarkImageDetails', {}).get('MarkImage', {}).get('MarkImageCategory', {}).get(
            'CategoryCodeDetails', {}).get('CategoryCode'):
        codes = data['MarkImageDetails']['MarkImage']['MarkImageCategory']['CategoryCodeDetails']['CategoryCode']
        biblio_data['code_531']['value'] = "<br>".join(codes)

    # 540 - зображення знака
    biblio_data['code_540'] = {
        'title': '(540) Зображення знака',
        'value': None
    }
    if data.get('MarkImageDetails', {}).get('MarkImage', {}):
        image_name = data['MarkImageDetails']['MarkImage']['MarkImageFilename']
        files_path = hit['Document']['filesPath']
        splitted_path = files_path.replace("\\", "/").split('/')
        splitted_path_len = len(splitted_path)
        biblio_data['code_540']['value'] = os.path.join(
            settings.MEDIA_URL,
            splitted_path[splitted_path_len - 4],
            splitted_path[splitted_path_len - 3],
            splitted_path[splitted_path_len - 2],
            image_name
        )

    # 591 - заявлені кольори (зазначення кольору чи поєднання кольорів, що охороняються)
    biblio_data['code_591'] = {
        'title': '(591) Заявлені кольори (зазначення кольору чи поєднання кольорів, що охороняються)',
        'value': None
    }
    if data.get('MarkImageDetails', {}).get('MarkImage', {}).get('MarkImageColourClaimedText'):
        colors = []
        for color in data['MarkImageDetails']['MarkImage']['MarkImageColourClaimedText']:
            colors.append(color['#text'])
        biblio_data['code_591']['value'] = "; ".join(colors)

    # 731 - заявник (ім'я або повне найменування та адреса заявника (заявників))
    biblio_data['code_731'] = {
        'title': '(731) Заявник (ім\'я або повне найменування та адреса заявника (заявників))',
        'value': None
    }
    if data.get('ApplicantDetails', {}).get('Applicant'):
        applicants = []
        for applicant in data['ApplicantDetails']['Applicant']:
            res = applicant.get(
                'ApplicantAddressBook', {}
            ).get(
                'FormattedNameAddress', {}
            ).get(
                'Name', {}
            ).get(
                'FreeFormatName', {}
            ).get(
                'FreeFormatNameDetails', {}
            ).get(
                'FreeFormatNameLine', ''
            )
            res += '<br>'
            res += applicant.get(
                'ApplicantAddressBook', {}
            ).get(
                'FormattedNameAddress', {}
            ).get(
                'Address', {}
            ).get(
                'FreeFormatAddress', {}
            ).get(
                'FreeFormatAddressLine', ''
            )
            res += '<br>'
            res += applicant.get(
                'ApplicantAddressBook', {}
            ).get(
                'FormattedNameAddress', {}
            ).get(
                'Address', {}
            ).get(
                'AddressCountryCode', ''
            )

            applicants.append(res)
        biblio_data['code_731']['value'] = ";<br>".join(applicants)

    # 740 - представник (ім'я, повне найменування та реєстраційний номер представника
    # у справах інтелектуальної влсності (патентного повіреного) або іншої довіреної особи)
    biblio_data['code_740'] = {
        'title': '(740) Представник (ім\'я, повне найменування та реєстраційний номер представника у справах '
                 'інтелектуальної влсності (патентного повіреного) або іншої довіреної особи)',
        'value': None
    }
    if data.get('RepresentativeDetails', {}).get('Representative'):
        representatives = []
        for representative in data['RepresentativeDetails']['Representative']:
            res = representative.get(
                'RepresentativeAddressBook', {}
            ).get(
                'FormattedNameAddress', {}
            ).get(
                'Name', {}
            ).get(
                'FreeFormatName', {}
            ).get(
                'FreeFormatNameDetails', {}
            ).get(
                'FreeFormatNameDetails', {}
            ).get(
                'FreeFormatNameLine', ''
            )
            res += '<br>'
            res += representative.get(
                'RepresentativeAddressBook', {}
            ).get(
                'FormattedNameAddress', {}
            ).get(
                'Address', {}
            ).get(
                'FreeFormatAddress', {}
            ).get(
                'FreeFormatAddressLine', ''
            )
            res += '<br>'
            res += representative.get(
                'RepresentativeAddressBook', {}
            ).get(
                'FormattedNameAddress', {}
            ).get(
                'Address', {}
            ).get(
                'AddressCountryCode', ''
            )

            representatives.append(res)
        biblio_data['code_740']['value'] = ";<br>".join(representatives)

    # 750 - адресат (адреса для листування)
    biblio_data['code_750'] = {
        'title': '(750) Адресат (адреса для листування)',
        'value': ''
    }
    if data.get('CorrespondenceAddress', {}).get('CorrespondenceAddressBook', {}).get('Name', {}).get(
            'FreeFormatNameLine'):
        biblio_data['code_750']['value'] = data['CorrespondenceAddress']['CorrespondenceAddressBook']['Name'][
            'FreeFormatNameLine']
        biblio_data['code_750']['value'] += '<br>'
    if data.get('CorrespondenceAddress', {}).get('CorrespondenceAddressBook', {}).get('Address', {}).get(
            'FreeFormatAddressLine'):
        biblio_data['code_750']['value'] += data['CorrespondenceAddress']['CorrespondenceAddressBook']['Address'][
            'FreeFormatAddressLine']
        biblio_data['code_750']['value'] += '<br>'
    if data.get('CorrespondenceAddress', {}).get('CorrespondenceAddressBook', {}).get('Address', {}).get(
            'AddressCountryCode'):
        biblio_data['code_750']['value'] += data['CorrespondenceAddress']['CorrespondenceAddressBook']['Address'][
            'AddressCountryCode']

    return biblio_data


def prepare_madrid_tm_data(app_number, record):
    """Подлготавливет данные о мадридских ТМ для отображения в бюлетне."""
    hit = record.to_dict()
    data = hit['MadridTradeMark']['TradeMarkDetails']
    biblio_data = dict()

    # (111) Номер міжнародної реєстрації
    biblio_data['code_111'] = {
        'title': '(111) Номер міжнародної реєстрації',
        'value': data['@INTREGN']
    }

    # 441 - Дата публікації заявки
    date_441 = EBulletinData.objects.filter(app_number=app_number).first().publication_date
    bul_num_441 = ClListOfficialBulletinsIp.objects.get(date_from__lte=date_441, date_to__gte=date_441)
    biblio_data['code_441'] = {
        'title': '(441) Дата публікації відомостей про міжнародну реєстрацію торговельної марки,'
                 ' що надійшла для проведення експертизи',
        'value': f"{date_441.strftime('%d.%m.%Y')}, бюл. № {bul_num_441.bul_number}"
    }

    # (450) Дата публікації відомостей про міжнародну реєстрацію та номер бюлетню Міжнародного бюро ВОІВ
    biblio_data['code_450'] = {
        'title': '(450) Дата публікації відомостей про міжнародну реєстрацію '
                 'та номер бюлетню Міжнародного бюро ВОІВ',
        'value': f"{datetime.datetime.strptime(data['ENN']['@PUBDATE'], '%Y-%m-%d').strftime('%d.%m.%Y')}, "
                 f"бюл. № {data['ENN']['@GAZNO']}"
    }

    # (151) Дата міжнародної реєстрації
    biblio_data['code_151'] = {
        'title': '(151) Дата міжнародної реєстрації',
        'value': datetime.datetime.strptime(data['@INTREGD'], '%Y-%m-%d').strftime('%d.%m.%Y')
    }

    # (891) Дата територіального поширення міжнародної реєстрації
    biblio_data['code_891'] = {
        'title': '(891) Дата територіального поширення міжнародної реєстрації',
        'value': datetime.datetime.strptime(data['@REGEDAT'], '%Y-%m-%d').strftime('%d.%m.%Y')
    }

    # (540) Зображення торговельної марки
    biblio_data['code_540'] = {
        'title': '(540) Зображення торговельної марки',
        'value': ''
    }
    splitted_path = hit['Document']['filesPath'].replace("\\", "/").split('/')
    splitted_path_len = len(splitted_path)
    image_dir = os.path.join(
        settings.MEDIA_ROOT,
        splitted_path[splitted_path_len - 5],
        splitted_path[splitted_path_len - 4],
        splitted_path[splitted_path_len - 3],
        splitted_path[splitted_path_len - 2]
    ).replace('madrid_tm', 'MADRID_TM').replace('reg_ua', 'REG_UA')
    images_url = os.path.join(
        settings.MEDIA_URL,
        splitted_path[splitted_path_len - 5],
        splitted_path[splitted_path_len - 4],
        splitted_path[splitted_path_len - 3],
        splitted_path[splitted_path_len - 2]
    ).replace('madrid_tm', 'MADRID_TM').replace('reg_ua', 'REG_UA')
    if os.path.exists(os.path.join(image_dir, f"{data['@INTREGN']}.jpg")):
        biblio_data['code_540']['value'] = os.path.join(images_url, f"{data['@INTREGN']}.jpg")
    elif os.path.exists(os.path.join(image_dir, f"{data['@INTREGN'][1:]}.jpg")):
        biblio_data['code_540']['value'] = os.path.join(images_url, f"{data['@INTREGN'][1:]}.jpg")

    # (511) Індекс (індекси) МКТП та перелік товарів і послуг
    biblio_data['code_511'] = {
        'title': '(511) Індекс (індекси) МКТП та перелік товарів і послуг',
        'value': None
    }
    if data.get('BASICGS', {}).get('GSGR'):
        classes = data['BASICGS']['GSGR']
        res = ''
        for c in classes:
            res += f"<strong>Кл. {c['@NICCLAI']}</strong>"
            if c.get('GSTERMEN'):
                res += f"<strong>:</strong> {c['GSTERMEN']}"
            if c.get('GSTERMFR'):
                res += f"<strong>:</strong> {c['GSTERMFR']}"
            res += "<br>"
        biblio_data['code_511']['value'] = res

    return biblio_data
