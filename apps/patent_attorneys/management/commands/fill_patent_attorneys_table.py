from django.core.management.base import BaseCommand
from ...models import PatentAttorneyExt

from django.db import connections


class Command(BaseCommand):
    help = 'Fills patent_attorneys_ext table'

    def handle(self, *args, **options):
        with connections['default'].cursor() as cursor:
            cursor.execute(f"TRUNCATE TABLE {PatentAttorneyExt._meta.db_table}")

        query = """
            INSERT INTO [10.10.18.1].UMA.dbo.patent_attorneys_ext (
                Reg_Num,
                Dat_Reg,
                Prizv,
                Name,
                Po_Batk,
                SEX,
                Dat_At_Kom,
                Num_At_Kom,
                Special,
                PostalAddress,
                Phones,
                E_Mail,
                Mis_Rob,
                PublicOrgs,
                EventList,
                SanctionsList,
                CompetenceList,
                LastUpdate 
            ) SELECT
            Reg_Num,
            Dat_Reg,
            Prizv,
            Name,
            Po_Batk,
            SEX,
            Dat_At_Kom,
            Num_At_Kom,
            Special,
            PostalAddress,
            Phones,
            E_Mail,
            Mis_Rob,
            PublicOrgs,
            EventList,
            SanctionsList,
            CompetenceList,
            LastUpdate 
            FROM
                v_PatentAttorneysListSIS
        """
        with connections['patent_attorneys'].cursor() as cursor:
            cursor.execute(query)
