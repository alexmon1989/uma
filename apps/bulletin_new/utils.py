from django.db.models import Prefetch, Q
from django.conf import settings
from .models import Bulletin, EBulletinData, EBulletinUnitHeader, EBulletinUnit, TransactionType
import datetime
import os


def get_bulletins():
    """Возвращает список бюлетней, по которым есть объекты."""
    bulletins = Bulletin.objects.raw(
        f'''
        SELECT DISTINCT
            YEAR(buls.Bull_Date) AS year, buls.Bull_Date AS bul_date, buls.Bull_Number AS bul_number, idBull
        FROM
            cl_list_official_bulletins_ip AS buls
            INNER JOIN {EBulletinData._meta.db_table} AS data
            ON ( data.publication_date = buls.Bull_Date )
        ORDER BY
            buls.Bull_Date
        '''
    )

    # Форматирование даты бюлетня
    return list(
        map(lambda item: [
            item.bul_date.year,
            item.bul_date.strftime("%d.%m.%Y"),
            item.bul_number,
            item.id
        ], bulletins)
    )


def get_bulletin_tree(bulletin_date):
    """Получение дерева бюлетня."""
    bulletin = Bulletin.objects.get(
        bul_date=datetime.datetime.strptime(bulletin_date, '%d.%m.%Y').strftime('%Y-%m-%d')
    )

    # Объекты ОПВ
    headers = EBulletinUnitHeader.objects.filter(
        ebulletinunit__ebulletindata__publication_date=bulletin.bul_date
    ).order_by(
        'header_ua'
    ).prefetch_related(
        Prefetch(
            'ebulletinunit_set',
            queryset=EBulletinUnit.objects.filter(
                ebulletindata__publication_date=bulletin.bul_date
            ).order_by(
                'unit_name_ua'
            ).distinct()
        ),
    ).distinct()

    # Построение дерева
    tree = []
    for header in headers:
        units = []

        # Типы объектов бюлетня
        for unit in header.ebulletinunit_set.all():
            units.append(
                {
                    'id': f"unit-{unit.id}",
                    'name': unit.unit_name_ua
                }
            )

        tree.append(
            {
                'id': f"header-{header.id}",
                'name': header.header_ua,
                'children': units
            }
        )

    # Оповещения (сповіщення)
    headers = EBulletinUnitHeader.objects.filter(pk=4).order_by(
        'header_ua'
    ).prefetch_related(
        Prefetch(
            'ebulletinunit_set',
            queryset=EBulletinUnit.objects.filter(
                obj_type__transactiontype__transaction__bulletin=bulletin
            ).order_by(
                'unit_name_ua'
            ).prefetch_related(
                Prefetch(
                    'obj_type__transactiontype_set',
                    queryset=TransactionType.objects.filter(
                        transaction__bulletin=bulletin
                    ).order_by(
                        'title'
                    ).distinct()
                )
            ).distinct()
        ),
    ).distinct()

    for header in headers:
        units = []

        # Типы объектов бюлетня
        for unit in header.ebulletinunit_set.all():
            transaction_types = []

            for transaction_type in unit.obj_type.transactiontype_set.all():
                transaction_types.append(
                    {
                        'id': f"transaction_type-{transaction_type.pk}",
                        'name': f"{transaction_type.title}",
                        'type': 'transaction_type',
                    }
                )

            units.append(
                {
                    'id': f"unit-{unit.id}",
                    'name': unit.obj_type.obj_type_ua,
                    'children': transaction_types
                }
            )

        tree.append(
            {
                'id': f"header-{header.id}",
                'name': header.header_ua,
                'children': units
            }
        )

    return tree


def fix_data_inv_um(data):
    """Исправляет данные в изобретениях и полезных моделях."""
    # Обработка I_71 для избежания ошибки добавления в индекс ElasticSearch
    i_71 = data.get('I_71', [])
    if type(i_71) is dict:
        i_71 = data['I_71']['I_71.N']
        data['I_71'] = i_71

    # Обработка I_72 для избежания ошибки добавления в индекс ElasticSearch
    for I_72 in data.get('I_72', []):
        if I_72.get('I_72.N'):
            I_72['I_72.N.E'] = I_72.pop('I_72.N')
        if I_72.get('I_72.C'):
            I_72['I_72.C.E'] = I_72.pop('I_72.C')

    # Обработка I_73 для избежания ошибки добавления в индекс ElasticSearch
    i_73 = data.get('I_73', [])
    if type(i_73) is dict:
        i_73 = data['I_73']['I_73.N']

    for item_i_73 in i_73:
        if item_i_73.get('I_73.N.U'):
            item_i_73['I_73.N'] = item_i_73.pop('I_73.N.U')
        if item_i_73.get('I_73.N.R'):
            item_i_73['I_73.N'] = item_i_73.pop('I_73.N.R')
        if item_i_73.get('I_73.N.E'):
            item_i_73['I_73.N'] = item_i_73.pop('I_73.N.E')
        if item_i_73.get('I_73.C.U'):
            item_i_73['I_73.C'] = item_i_73.pop('I_73.C.U')
        if item_i_73.get('I_73.C.R'):
            item_i_73['I_73.C'] = item_i_73.pop('I_73.C.R')
        if item_i_73.get('I_73.C.E'):
            item_i_73['I_73.C'] = item_i_73.pop('I_73.C.E')
    data['I_73'] = i_73

    # Обработка I_98.Index
    if data.get('I_98.Index') is not None:
        data['I_98_Index'] = data.pop('I_98.Index')


def fix_data_id(data):
    """Исправляет данные в пром. образцах."""
    # Формат МКПЗ
    for item in data['Design']['DesignDetails'].get('IndicationProductDetails', {}):
        cl = item.get('Class')
        if cl:
            cl_l = cl.split('-')
            if len(cl_l[1]) == 1:
                cl_l[1] = f"0{cl_l[1]}"
            item['Class'] = '-'.join(cl_l)


def fix_data_tm(data):
    """Исправляет данные в торговых марках."""
    # Форматирование даты
    if data['TradeMark'].get('PublicationDetails', {}).get('PublicationDate'):
        try:
            d = datetime.datetime.today().strptime(
                data['TradeMark']['PublicationDetails']['PublicationDate'],
                '%d.%m.%Y'
            )
        except ValueError:
            pass
        else:
            data['TradeMark']['PublicationDetails']['PublicationDate'] = d.strftime('%Y-%m-%d')

    # Поле 441 (дата опубликования заявки)
    try:
        e_bulletin_app = EBulletinData.objects.get(
            app_number=data['TradeMark']['TrademarkDetails'].get('ApplicationNumber')
        )
    except EBulletinData.DoesNotExist:
        pass
    else:
        data['TradeMark']['TrademarkDetails']['Code_441'] = e_bulletin_app.publication_date


def prepare_madrid_tm_data(biblio_data, app):
    """Подлготавливет данные о мадридских ТМ для отображения в бюлетне."""
    # (111) Номер міжнародної реєстрації
    biblio_data['code_111'] = biblio_data['@INTREGN']

    # 441 - Дата публікації заявки
    date_441 = EBulletinData.objects.filter(app_number=biblio_data['@INTREGN']).first().publication_date
    biblio_data['code_441'] = date_441.strftime('%d.%m.%Y')
    bul_num_441 = Bulletin.objects.get(date_from__lte=date_441, date_to__gte=date_441)
    biblio_data['code_441_bul_number'] = bul_num_441.bul_number

    # (450) Дата публікації відомостей про міжнародну реєстрацію та номер бюлетню Міжнародного бюро ВОІВ
    biblio_data['code_450'] = f"{datetime.datetime.strptime(biblio_data['ENN']['@PUBDATE'], '%Y%m%d').strftime('%d.%m.%Y')}" \
                              f", бюл. № {biblio_data['ENN']['@GAZNO']}"

    # (151) Дата міжнародної реєстрації
    biblio_data['code_151'] = datetime.datetime.strptime(biblio_data['@INTREGD'], '%Y%m%d').strftime('%d.%m.%Y')

    # (891) Дата територіального поширення міжнародної реєстрації
    biblio_data['code_891'] = datetime.datetime.strptime(biblio_data['@REGEDAT'], '%Y%m%d').strftime('%d.%m.%Y')

    # (540) Зображення торговельної марки
    splitted_path = app.app.files_path.replace("\\", "/").split('/')
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

    if os.path.exists(os.path.join(image_dir, f"{biblio_data['@INTREGN']}.jpg")):
        biblio_data['code_540'] = os.path.join(images_url, f"{biblio_data['@INTREGN']}.jpg")
    elif os.path.exists(os.path.join(image_dir, f"{biblio_data['@INTREGN'][1:]}.jpg")):
        biblio_data['code_540'] = os.path.join(images_url, f"{biblio_data['@INTREGN'][1:]}.jpg")

    return biblio_data
