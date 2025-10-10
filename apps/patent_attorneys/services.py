import json

from apps.patent_attorneys.models import PatentAttorneyNew, PatentAttorneyExt


def patent_attorney_fill_db_old_db() -> None:
    reg_nums = PatentAttorneyNew.objects.values_list('reg_num', flat=True)

    for item in PatentAttorneyExt.objects.exclude(reg_num__in=reg_nums):
        patent_attorney = PatentAttorneyNew()

        patent_attorney.reg_num = item.reg_num
        patent_attorney.dat_reg = item.dat_reg
        patent_attorney.prizv = item.prizv
        patent_attorney.name = item.name
        patent_attorney.po_batk = item.po_batk
        if item.sex == 1:
            patent_attorney.sex = 'Чоловік'
        elif item.sex == 0:
            patent_attorney.sex = 'Жінка'
        patent_attorney.dat_at_kom = item.dat_at_kom
        patent_attorney.num_at_kom = item.num_at_kom
        patent_attorney.special = item.special
        patent_attorney.postaladdress = item.postaladdress
        patent_attorney.phones = item.phones
        patent_attorney.e_mail = item.e_mail
        patent_attorney.mis_rob = item.mis_rob
        patent_attorney.public_orgs = item.public_orgs
        patent_attorney.event_list = item.event_list
        patent_attorney.competence_list = item.competence_list
        patent_attorney.last_update = item.last_update

        patent_attorney.save()


def patent_attorney_fill_db_from_file(file_name: str) -> None:
    with open(file_name) as f:
        data = json.load(f)
        for item in data.values():
            patent_attorney = PatentAttorneyNew()

            patent_attorney.pat_id = item['id']
            patent_attorney.reg_num = item['Reg_Num']
            patent_attorney.dat_reg = item['Dat_Reg'][:-1]
            patent_attorney.prizv = item['Prizv']
            patent_attorney.name = item['Name']
            patent_attorney.po_batk = item['Po_Batk']
            patent_attorney.sex = item['SEX']
            patent_attorney.dat_at_kom = item['Dat_At_Kom'][:-1]
            patent_attorney.num_at_kom = item['Num_At_Kom']
            patent_attorney.special = item['Special'].replace(',', ', ').lower().capitalize()
            patent_attorney.postaladdress = item['PostalAddress']
            patent_attorney.phones = item['Phones']
            patent_attorney.e_mail = item['E_Mail']
            patent_attorney.mis_rob = item['Mis_Rob']
            patent_attorney.public_orgs = item['PublicOrgs']
            if item['EventList'] and not item['EventList'].startswith('null'):
                patent_attorney.event_list = item['EventList']
            patent_attorney.competence_list = item['CompetenceList']
            patent_attorney.last_update = item['LastUpdate'][:-1]

            patent_attorney.save()
