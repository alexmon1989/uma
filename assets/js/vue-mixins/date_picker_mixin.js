export default {
    methods: {
        // Обработчик нажатия на "ОК" компонента выбора даты.
        onDateConfirm: function (val) {
            if (val[0] || val[1]) {
                if (!val[0]) {
                    this.value = ["01.01.1900", val[1]];
                } else if (!val[1]) {
                    let today = new Date();
                    let dd = String(today.getDate()).padStart(2, '0');
                    let mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
                    let yyyy = today.getFullYear();

                    // this.$emit('input', [val[0], dd + '.' + mm + '.' + yyyy])
                    this.value = [val[0], dd + '.' + mm + '.' + yyyy];
                }
            }
        }
    }
};
