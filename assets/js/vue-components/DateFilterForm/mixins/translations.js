export const translations = {
    data() {
        return {
            translations: {
                label: gettext('Фільтр по даті'),
                filter: gettext('Фільтрувати'),
                validationErrors: {
                    required: gettext('Обов\'язкове поле для заповнення'),
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
