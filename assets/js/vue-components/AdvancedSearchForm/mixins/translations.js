export const translations = {
    data() {
        return {
            translations: {
                startText: gettext('Для початку роботи заповніть форму пошуку'),
                selectParameter: gettext('Оберіть параметр пошуку'),
                value: gettext('Значення'),
                addBtnText: gettext('Додати параметр'),
                searchBtnText: gettext('Показати результати'),
                performingSearch: gettext('Виконуємо пошук...'),
                objType: gettext('Об\'єкт промислової власності'),
                objState: gettext('Правовий статус ОПВ'),
                ipcCode: gettext('Бібліографічні елементи'),
                validationErrors: {
                    required: gettext('Обов\'язкове поле для заповнення'),
                    validQuery: gettext('Поле містить невірне значення'),
                },
                transactionDateLang: {
                    days: [
                        gettext('Нд'),
                        gettext('Пн'),
                        gettext('Вт'),
                        gettext('Ср'),
                        gettext('Чт'),
                        gettext('Пт'),
                        gettext('Сб')
                    ],
                    months: [
                        gettext('Січень'),
                        gettext('Лютий'),
                        gettext('Березень'),
                        gettext('Квітень'),
                        gettext('Травень'),
                        gettext('Червень'),
                        gettext('Липень'),
                        gettext('Серпень'),
                        gettext('Вересень'),
                        gettext('Жовтень'),
                        gettext('Листопад'),
                        gettext('Грудень')
                    ],
                    pickers: [
                        gettext('наступні 7 днів'),
                        gettext('наступні 30 днів'),
                        gettext('попередні 7 днів'),
                        gettext('попередні 30 днів')
                    ],
                    placeholder: {
                        date: gettext('Оберіть дату'),
                        dateRange: gettext('Оберіть діапазон дат')
                    }
                },
            },
        }
    }
};
