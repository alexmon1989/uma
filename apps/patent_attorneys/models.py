from django.db import models


class PatentAttorney(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    reg_num = models.IntegerField(db_column='Reg_Num', blank=True, null=True)
    dat_reg = models.DateTimeField(db_column='Dat_Reg', blank=True, null=True)
    dat_at_kom = models.DateTimeField(db_column='Dat_At_Kom', blank=True, null=True)
    num_at_kom = models.IntegerField(db_column='Num_At_Kom', blank=True, null=True)
    dat_nakaz = models.DateTimeField(db_column='Dat_Nakaz', blank=True, null=True)
    num_nakaz = models.IntegerField(db_column='Num_Nakaz', blank=True, null=True)
    prizv = models.CharField(db_column='Prizv', max_length=50, blank=True, null=True)
    name = models.CharField(db_column='Name', max_length=50, blank=True, null=True)
    po_batk = models.CharField(db_column='Po_Batk', max_length=50, blank=True, null=True)
    special = models.CharField(db_column='Special', max_length=500, blank=True, null=True)
    mis_rob = models.CharField(db_column='Mis_Rob', max_length=450, blank=True, null=True)
    list_index = models.CharField(db_column='List_Index', max_length=10, blank=True, null=True)
    list_oblast = models.CharField(db_column='List_Oblast', max_length=300, blank=True, null=True)
    list_misto = models.CharField(db_column='List_Misto', max_length=300, blank=True, null=True)
    list_street = models.CharField(db_column='List_Street', max_length=300, blank=True, null=True)
    prog_index = models.CharField(db_column='Prog_Index', max_length=10, blank=True, null=True)
    prog_oblast = models.CharField(db_column='Prog_Oblast', max_length=30, blank=True, null=True)
    prog_misto = models.CharField(db_column='Prog_Misto', max_length=30, blank=True, null=True)
    prog_street = models.CharField(db_column='Prog_Street', max_length=300, blank=True, null=True)
    e_mail = models.CharField(db_column='E_Mail', max_length=300, blank=True, null=True)
    phones = models.CharField(db_column='Phones', max_length=300, blank=True, null=True)
    fax = models.CharField(db_column='Fax', max_length=300, blank=True, null=True)
    web_site = models.CharField(db_column='Web_Site', max_length=300, blank=True, null=True)
    stupin = models.CharField(db_column='Stupin', max_length=300, blank=True, null=True)
    other = models.CharField(db_column='Other', max_length=300, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'patent_attorneys'
        ordering = ('reg_num',)


class PatentAttorneyExt(models.Model):
    id = models.AutoField(db_column='Id', primary_key=True)
    reg_num = models.IntegerField(db_column='Reg_Num', blank=True, null=True)
    dat_reg = models.DateTimeField(db_column='Dat_Reg', blank=True, null=True)
    prizv = models.CharField(db_column='Prizv', max_length=50, blank=True, null=True)
    name = models.CharField(db_column='Name', max_length=50, blank=True, null=True)
    po_batk = models.CharField(db_column='Po_Batk', max_length=50, blank=True, null=True)
    sex = models.BooleanField(db_column='SEX', blank=True, null=True)
    dat_at_kom = models.DateTimeField(db_column='Dat_At_Kom', blank=True, null=True)
    num_at_kom = models.IntegerField(db_column='Num_At_Kom', blank=True, null=True)
    special = models.CharField(db_column='Special', max_length=500, blank=True, null=True)
    postaladdress = models.CharField(db_column='PostalAddress', max_length=255, blank=True, null=True)
    phones = models.CharField(db_column='Phones', max_length=300, blank=True, null=True)
    e_mail = models.CharField(db_column='E_Mail', max_length=300, blank=True, null=True)
    mis_rob = models.CharField(db_column='Mis_Rob', max_length=450, blank=True, null=True)
    public_orgs = models.TextField(db_column='PublicOrgs', max_length=8000, blank=True, null=True)
    event_list = models.TextField(db_column='EventList', max_length=8000, blank=True, null=True)
    competence_list = models.TextField(db_column='CompetenceList', max_length=8000, blank=True, null=True)
    sanctions_list = models.TextField(db_column='SanctionsList', max_length=8000, blank=True, null=True)
    last_update = models.DateTimeField(db_column='LastUpdate', blank=True, null=True)

    class Meta:
        db_table = 'patent_attorneys_ext'
        ordering = ('reg_num',)
