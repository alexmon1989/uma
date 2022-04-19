import axios from 'axios';

export default {
    created() {
        // Проверка корректности номера заявки
        this.$validator.extend('validApplication', {
            validate: (value) => {
                return axios.get('/payments/api/validate-application/' + this.group.id + '/' + value + '/')
                  .then((response) => {
                    return response.data.result;
                  });
            }
        });
    }
}
