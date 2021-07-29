export const translations = {
    data() {
        return {
            translations: {
                valueFieldPlaceholder: gettext('Введіть суму, яку бажаєте сплатити'),
                valueFieldLabel: gettext('Сума до сплати, грн'),

                appNumberFieldLabel: gettext('Номер заявки'),
                appNumberFieldPlaceholder: gettext('Введіть номер заявки'),

                groupFieldLabel: gettext('Група зборів'),
                groupFieldPlaceholder: gettext('Оберіть групу зборів'),

                feeTypeFieldLabel: gettext('Вид збору'),
                feeTypeFieldPlaceholder: gettext('Оберіть тип збору'),

                btnText: gettext('Сформувати замовлення'),

                validationErrors: {
                    required: gettext('Обов\'язкове поле для заповнення'),
                    integer: gettext('Поле має містити ціле число'),
                    validApplication: gettext('Заявку в обраній групі зборів не знайдено'),
                },
            },
        }
    }
};
