Додання інформації у пошуковий індекс
=====================================

Додання інформації у пошуковий індекс (далі - індексація) відбувається за допомогою виклику команди **search_indexation**.
Для цього необхідно виконати наступне:

1. Підключитися до серверу **panda (10.11.11.51)** по протоколу **SSH** (22-й порт) за допомогою будь-якого зручного клієнта (наприклад, **Putty**).
2. Перейти у каталог */home/developer/projects/uma*:

.. code-block:: bash

   cd /home/developer/projects/uma

3. Виконати команду:

.. code-block:: bash

   poetry run python manage.py search_indexation

За замовченням (якщо не вказано параметри при виклику команди) індексація відбувається для об'єктів, 
які у БД [UMA].[IPC_APPList] мають значення *0* у полі *ElasticIndexed*.

Параметри команди search_indexation
-----------------------------------


**Список доступних параметрів**:

--id
    Ідентифікатор об'єкта. 

    Можна взяти з посилання на сторінку об'єкта 
    (наприклад, у об'єкта https://sis.nipo.gov.ua/uk/search/detail/1791163/ ідентифікатором є 1791163), 
    або з таблиці БД [UMA].[IPC_APPList] (поле idAPPNumber є ідентифікатором)

--obj_type
    Тип об'єкта

    Можливі значення:
        * 1 - Винаходи
        * 2 - Корисні моделі
        * 3 - Топографії інтегральних мікросхем
        * 4 - Торговельні марки
        * 5 - Географічні зазначення
        * 6 - Промислові зразки
        * 9 - Міжнародні реєстрації торговельних марок з поширенням на територію України
        * 10 - Авторське право на твір
        * 11 - Договір про передачу права на використання твору
        * 12 - Договір про передачу (відчуження) майнових прав на твір
        * 13 - Авторське право на службовий твір
        * 14 - Міжнародні реєстрації торговельних марок, зареєстровані в Україні
        * 16 - Сертифікат додаткової охорони прав на винахід

    Фактично є значенням поля *idObjType* об'єктів(а) у таблиці БД *[UMA].[IPC_APPList]*.

    За замовченням (якщо параметр не вказано при виклику команди), відбувається індексація об'єктів без урахування 
    типів об'єктів.

--status
    Статус об'єкта

    Можливі значення:
        * 1 - Заявка
        * 2 - Охоронний документ

    За замовченням (якщо параметр не вказано при виклику команди), відбувається індексація об'єктів без урахування 
    статусів об'єктів.

--ignore_indexed
    Ігнорувати значення поля *ElasticIndexed* об'єктів(а) у таблиці БД *[UMA].[IPC_APPList]*.

    Можливі значення:
        * 0 - Не ігнорувати
        * 1 - Ігнорувати

    За замовченням (якщо параметр не вказано при виклику команди), відбувається індексація об'єктів, 
    які у таблиці БД *[UMA].[IPC_APPList]* мають значення *0* у полі *ElasticIndexed*.

Приклади виклику команди search_indexation з параметрами
--------------------------------------------------------

Додати у пошуковий індекс об'єкт з ідентифікатором 1791163 та ігнорувати ознаку того, що його вже було проіндексовано:

.. code-block:: bash

   poetry run python manage.py search_indexation --id=1791163 --ignore_indexed=1
   
Додати у пошуковий індекс тільки непроіндексовані торговельні марки:

.. code-block:: bash

   poetry run python manage.py search_indexation --obj_type=4

Можливі помилки при індексації
------------------------------

При запуску команди індексації виводиться її лог, в тому числі і помилки, при наявності яких запис у пошуковий 
індекс неможливий. Нижче наведено опис можливих помилок та спосіб їх вирішення:

1. **Transaction date cannot be in future time: m202400001**. Помилка означає, що у даних заявки m202400001 є 
сповіщення, дата яких вказана у майбутньому часі (відносно часу запуску команди індексації). Усувати таку помилку не 
потрібно, оскілки дані будуть успішно проіндексовані коли "майбутніх сповіщень" у даних не буде.

2. **Publication date cannot be in future time: a202400001**. Помилка означає, що у даних заявки a202400001 є 
інформація про публікацію заявки у майбутньому часі (відносно часу запуску команди індексації). Усувати таку помилку не 
потрібно, оскілки дані будуть успішно проіндексовані коли дата публікації перестане бути майбутньою.

3. **JSONDecodeError with encoding utf-16: Expecting ',' delimiter: line 38 column 7 (char 909): /mnt/bear/INVENTIONS/2014/a201408110/a201408110.json**. 
Помилка с типом **JSONDecodeError** означає, що у файлі з даними 
(в даному випадку */mnt/bear/INVENTIONS/2014/a201408110/a201408110.json*) є помилка структури/синтаксису JSON. 
Для усунення необхідно відредагувати файл та пересвідчитися, що він має коректну структуру/синтаксис.

4. **FileNotFoundError: [Errno 2] No such file or directory: '/mnt/bear/TRADE_MARKS/2024/m202400001/m202400001.json'**
Помилка с типом **FileNotFoundError** означає, що файл з даними заявки відсутній.
Для усунення необхідно створити файл з даними за вказаним шляхом.


Поточний розклад автоматичного запуску індексації за допомогою crontab
----------------------------------------------------------------------

Запуск команд відбувається на сервері **panda (10.11.11.51)**.

.. code-block:: bash

    # Індексація усіх об'єктів кожного ранку о 6-ій ранку крім середи
    0 6 * * 0-2,4-6 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation 2>&1 | /bin/mail -v -s "Search Indexation Log" a.monastyretsky@nipo.gov.ua
    
    # Індексація усіх об'єктів у середу о 12 дня
    0 12 * * 3 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation 2>&1 | /bin/mail -v -s "Search Indexation Log" a.monastyretsky@nipo.gov.ua
    
    # Індексація міжнародки у четвер о 9 ранку
    0 9 * * 4 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation --obj_type=9 &> /dev/null
    0 9 * * 4 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation --obj_type=14 &> /dev/null
        
    # Індексація ТМ та ПЗ кожної години (крім вівторка та середи)
    0 1-5,8-23 * * 0-1,4-6 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation --obj_type=4 &> /dev/null
    0 1-5,8-23 * * 0-1,4-6 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation --obj_type=6 &> /dev/null
    
    # Індексація ТМ та ПЗ кожної години у вівторок
    0 1-5,8-17 * * 2 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation --obj_type=4 &> /dev/null
    0 1-5,8-17 * * 2 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation --obj_type=6 &> /dev/null
    
    # Індексація ТМ та ПЗ кожної години у середу
    0 13-23 * * 3 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation --obj_type=4 &> /dev/null
    0 13-23 * * 3 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation --obj_type=6 &> /dev/null
    
Слід зазначити, що окремий розклад на вівторок та середу необхідний для того, щоб призупинити індексацію з 17 години 
у вівторок до 12 години у середу для того щоб був час на редагування обмежених публікацій.

Редагування розкладу автоматичного запуску індексації за допомогою crontab
--------------------------------------------------------------------------

Для редагування розкладу необхідно:

1. Підключитися до серверу **panda (10.11.11.51)** по протоколу **SSH** (22-й порт) за допомогою будь-якого зручного клієнта (наприклад, **Putty**).
2. Виконати команду:

.. code-block:: bash

   sudo -i
   
3. Внести зміни та зберігти зміни. За замовчуванням редагування відбувається за допомогою редактора **vim**.


У разі якщо необхідно отримувати лог роботи індексатора на пошту, то вивід варто перенаправляти на команду 
*"/bin/mail"*, наприклад:

.. code-block:: bash

    0 12 * * 3 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py search_indexation 2>&1 | /bin/mail -v -s "Search Indexation Log" a.monastyretsky@nipo.gov.ua

Для налаштування команди *"/bin/mail"* необхідно виконати відповідні налаштування: :ref:`mailx_settings`.
