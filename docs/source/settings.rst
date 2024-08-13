Налаштування
============


.. _mailx_settings:

Поштовий агент (сервер panda)
-----------------------------

У якості поштового агента на сервері panda використовується утіліта `mailx <https://pubs.opengroup.org/onlinepubs/9699919799/utilities/mailx.html>`_.

Поштовий агент необхідно налаштувати передусім для роботи команди **mail**.

Налаштування агенту зберігаються у файлі */etc/mail.rc*. Основні з них знаходяться у кінці файлу:

.. code-block:: bash

    set smtp=10.10.16.1:25
    set from=sis@ukrpatent.org
    set ssl-verify=ignore
    set nss-config-dir=/etc/pki/nssdb/

Для тестування коректності роботи достатньо виконати команду (адресата необхідно замінити на бажаного):

.. code-block:: bash

    echo "Your message" | mail -v -s "Message Subject" a.monastyretsky@nipo.gov.ua
