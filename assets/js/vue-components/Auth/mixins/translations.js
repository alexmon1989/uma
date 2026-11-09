export const translations = {
    data() {
        return {
            translations: {
                // Tab labels
                tabFileKey: gettext('За допомогою файлового ключа'),
                tabTokenKey: gettext('За допомогою токена'),
                tabPassword: gettext('За допомогою логіна/пароля'),

                // Common / Select CA
                selectCA: gettext('Оберіть ЦСК:'),
                autoDetectCA: gettext('Визначити автоматично'),
                otherCA: gettext('інший'),
                rememberMe: gettext("Запам'ятати"),
                login: gettext('Вхід'),
                loading: gettext('Завантаження...'),
                cryptoLoading: gettext('Завантаження криптографічної бібліотеки'),

                // LoginFileKey labels & placeholders
                privateKey: gettext('Особистий ключ'),
                browse: gettext('Огляд'),
                certificates: gettext('Сертифікат(и)'),
                chooseCertsHint: gettext('Оберіть файл(и) з сертифікатом(ами) (зазвичай, з розширенням cer, crt)'),
                keyPassword: gettext('Пароль захисту ключа'),

                // LoginHardwareKey labels & placeholders
                hardwareMedia: gettext('Захищений носій (токен):'),
                selectHardwareMedia: gettext('Оберіть носій ключа'),
                noHardwareMediaFound: gettext('Носії не знайдено (підключіть токен)'),
                refreshMedia: gettext('Оновити'),
                tokenPassword: gettext('Пароль захисту токена (PIN-код)'),
                noTokenSelected: gettext('Оберіть захищений носій (токен)'),
                noTokenPassword: gettext('Вкажіть пароль захисту токена (PIN-код)'),
                softwareNotSupported: gettext('Бібліотека web-підпису не підтримується у вашому браузері або ОС.'),
                softwareNeedUpdate: gettext('Бібліотека web-підпису потребує оновлення.'),
                softwareNeedInstall: gettext('Для роботи з токенами необхідно встановити програмне забезпечення web-підпису.'),
                webExtensionNeedInstall: gettext('Також необхідно встановити розширення для браузера.'),
                downloadSoftware: gettext('Завантажити модуль web-підпису'),
                installExtension: gettext('Встановити розширення для браузера'),
                checkAgain: gettext('Перевірити знову'),

                // Hints
                choosePKFileText: gettext("Оберіть файл з особистим ключем (зазвичай його назва \"Key-6.dat\" або *.pfx, *.pk8, *.zs2, *.jks) та вкажіть пароль захисту"),
                choosePKCertText: gettext(', а також оберіть сертифікат(и)'),

                // Errors - Common & File Key
                authFailed: gettext('Авторизація неможлива!'),
                authError: gettext('Виникла помилка при авторизації'),
                cryptoNotLoaded: gettext('Криптографічну бібліотеку не завантажено. Перевірте підключення euscp.js.'),
                cryptoInitError: gettext('Помилка ініціалізації криптографічної бібліотеки'),
                initializingWait: gettext('Зачекайте, триває ініціалізація криптографічного модуля...'),
                noKeySelected: gettext('Оберіть файл з особистим ключем'),
                noCertSelected: gettext('Оберіть файл(и) з сертифікатом(ами)'),
                noPassword: gettext('Вкажіть пароль доступу до особистого ключа'),
                jksNoKeys: gettext('У JKS контейнері не знайдено ключів'),

                // LoginPassword labels & placeholders
                usernameLabel: gettext('Логін:'),
                usernamePlaceholder: gettext('Логін'),
                passwordLabel: gettext('Пароль:'),
                passwordPlaceholder: gettext('Пароль'),

                // Errors - Password
                emptyCredentials: gettext('Будь ласка, вкажіть логін та пароль.'),
                invalidCredentials: gettext('Невірний логін або пароль.'),
            }
        };
    }
};
