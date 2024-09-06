from django.db import models


class WKMMark(models.Model):
    id = models.AutoField(db_column='IdMark', primary_key=True)
    decision_date = models.DateTimeField(
        db_column='DecisionDate',
        verbose_name='Дата набрання чинності рішенням, яким визнано, що знак став добре відомим в Україні',
        blank=True,
        help_text='Не виводиться, якщо заповнене поле "Рішення суду (укр.)"'
    )
    order_date = models.DateTimeField(
        db_column='OrderDate',
        verbose_name='Дата наказу',
        blank=True,
        help_text='Не виводиться, якщо заповнене поле "Рішення суду (укр.)"'
    )
    order_number = models.CharField(
        db_column='OrderNumber',
        max_length=50,
        blank=True,
        verbose_name='Номер наказу',
        help_text='Не виводиться, якщо заповнене поле "Рішення суду (укр.)"'
    )
    rights_date = models.DateTimeField(
        db_column='RightsDate',
        verbose_name='Дата, на яку знак став добре відомим в Україні'
    )
    keywords = models.CharField(
        db_column='KeyWords',
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Ключові слова'
    )
    mark_image = models.BinaryField(db_column='MarkImage', blank=True, null=True, editable=True)
    state_id = models.SmallIntegerField(db_column='IdState', default=1)
    bulletin = models.ForeignKey(
        'WKMRefBulletin',
        db_column='IdBulletin',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        verbose_name='Бюлетень'
    )
    where_to_publish = models.CharField(db_column='wheretopublish', max_length=20, default='both')
    court_comments_ua = models.CharField(
        db_column='courtcomments', max_length=255, blank=True, null=True, verbose_name='Рішення суду (укр.)'
    )
    court_comments_rus = models.CharField(
        db_column='courtcommentsRUS', max_length=255, blank=True, null=True, verbose_name='Рішення суду (рос.)'
    )
    court_comments_eng = models.CharField(
        db_column='courtcommentsENG', max_length=255, blank=True, null=True, verbose_name='Рішення суду (анг.)'
    )

    owners = models.ManyToManyField('WKMRefOwner', through='WKMMarkOwner')

    def __str__(self):
        return self.keywords

    class Meta:
        managed = False
        db_table = 'Mark'
        verbose_name = 'Добре відома ТМ'
        verbose_name_plural = 'Добре відомі ТМ'


class WKMRefOwner(models.Model):
    id = models.AutoField(db_column='IdOwner', primary_key=True)
    owner_name = models.CharField(db_column='OwnerName', max_length=500, verbose_name='Найменування власника')
    country_code = models.CharField(db_column='CountryCode', max_length=2, verbose_name='Код країни')

    def __str__(self):
        return f"{self.owner_name} [{self.country_code}]"

    class Meta:
        managed = False
        db_table = 'ref_Owners'
        verbose_name = 'Власник'
        verbose_name_plural = 'Власники'
        ordering = ('owner_name',)


class WKMMarkOwner(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    mark = models.ForeignKey(WKMMark, db_column='IdMark', on_delete=models.DO_NOTHING)
    owner = models.ForeignKey(WKMRefOwner, on_delete=models.DO_NOTHING, db_column='IdOwner',
                              verbose_name='Найменування власника')
    ord_num = models.SmallIntegerField(db_column='OrdNum', verbose_name='Порядок відображення')

    def __str__(self):
        return str(self.owner)

    class Meta:
        verbose_name = 'Власник'
        verbose_name_plural = 'Власники'
        managed = False
        db_table = 'MarkOwners'


class WKMClass(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    mark = models.ForeignKey(WKMMark, db_column='IdMark', on_delete=models.DO_NOTHING)
    class_number = models.SmallIntegerField(
        db_column='ClassNumber', unique=False, verbose_name='Номер класу'
    )
    ord_num = models.SmallIntegerField(db_column='OrdNum', verbose_name='Порядок відображення')
    products = models.CharField(db_column='Products', max_length=2000, verbose_name='Перелік товарів')

    def __str__(self):
        return str(self.class_number)

    class Meta:
        managed = False
        db_table = 'MarkProducts'
        verbose_name = 'Клас'
        verbose_name_plural = 'Ніццька класифікація'


class WKMRefBulletin(models.Model):
    id = models.AutoField(db_column='IdBulletin', primary_key=True)
    bulletin_date = models.DateTimeField(db_column='BulletinDate', verbose_name='Дата бюлетеня')
    bulletin_number = models.CharField(db_column='BulletinNumber', max_length=50, verbose_name='Номер бюлетеня')
    bull_str = models.CharField(
        db_column='bullStr',
        max_length=10,
        verbose_name='Коротка форма запису номера та дати бюлетеня'
    )

    class Meta:
        managed = False
        db_table = 'ref_Bulletins'
        verbose_name = 'Бюлетень'
        verbose_name_plural = 'Список бюлетенів'

    def __str__(self):
        return self.bull_str


class WKMVienna(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    mark = models.ForeignKey(WKMMark, db_column='IdMark', on_delete=models.DO_NOTHING)
    class_number = models.CharField(
        db_column='ClassNumber', max_length=255, unique=False, verbose_name='Номер класу'
    )

    def __str__(self):
        return str(self.class_number)

    class Meta:
        managed = False
        db_table = 'MarkVienna'
        verbose_name = 'Клас'
        verbose_name_plural = 'Віденська класифікація'


class WKMDocumentType(models.Model):
    value = models.CharField('Значення', max_length=255)
    code = models.CharField('Код типу документа', max_length=32, blank=True, null=True)

    def __str__(self):
        return self.value

    class Meta:
        managed = False
        db_table = 'ref_DocumentTypes'
        verbose_name = 'Тип документа'
        verbose_name_plural = 'Типи документів'


class WKMDocument(models.Model):
    """Модель документу добре відомої ТМ."""
    document_type = models.ForeignKey(
        WKMDocumentType,
        on_delete=models.SET_NULL,
        verbose_name='Тип документа',
        null=True,
        db_column='IdDocumentType'
    )
    wkm = models.ForeignKey(WKMMark,
                            on_delete=models.SET_NULL,
                            verbose_name='Добре відома ТМ',
                            null=True,
                            db_column='IdMark')
    file = models.BinaryField(blank=True, null=True, editable=True, verbose_name='Файл')

    class Meta:
        managed = False
        db_table = 'MarkDocuments'
        verbose_name = 'Документ'
        verbose_name_plural = 'Документи'

    def __str__(self):
        return self.document_type.value
