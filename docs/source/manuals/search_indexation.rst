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

Поточний розклад автоматичного запуску індексації за допомогою crontab
----------------------------------------------------------------------

Запуск команд відбувається на сервері **panda (10.11.11.51)**.

.. code-block:: bash

    # Індексація усіх об'єктів кожного ранку о 6-ій ранку крім середи
    0 6 * * 0-2,4-6 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch &> /dev/null
    
    # Індексація усіх об'єктів у середу о 12 дня
    0 12 * * 3 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch &> /dev/null
    
    # Індексація міжнародних ТМ у четвер о 9 ранку
    0 9 * * 4 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch --obj_type=9 &> /dev/null
    0 9 * * 4 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch --obj_type=14 &> /dev/null
        
    # Індексація ТМ та ПЗ кожної години (крім вівторка та середи)
    0 1-5,8-23 * * 0-1,4-6 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch --obj_type=4 &> /dev/null
    0 1-5,8-23 * * 0-1,4-6 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch --obj_type=6 &> /dev/null
    
    # Індексація ТМ та ПЗ кожної години у вівторок
    0 1-5,8-17 * * 2 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch --obj_type=4 &> /dev/null
    0 1-5,8-17 * * 2 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch --obj_type=6 &> /dev/null
    
    # Індексація ТМ та ПЗ кожної години у середу
    0 13-23 * * 3 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch --obj_type=4 &> /dev/null
    0 13-23 * * 3 /home/developer/.cache/pypoetry/virtualenvs/uma-0wrnzTc1-py3.10/bin/python /home/developer/projects/uma/manage.py add_docs_to_elasticsearch --obj_type=6 &> /dev/null

Для редагування розкладу необхідно:

1. Підключитися до серверу **panda (10.11.11.51)** по протоколу **SSH** (22-й порт) за допомогою будь-якого зручного клієнта (наприклад, **Putty**).
2. Виконати команду:

.. code-block:: bash

   sudo -i
   
3. Внести зміни та зберігти зміни. За замовчуванням редагування відбувається за допомогою редактора **vim**.
