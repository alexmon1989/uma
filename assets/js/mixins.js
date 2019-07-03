import axios from 'axios';

export default {
    methods: {
        // Получает статус и результат выполнения задачи
        getTaskInfo: function (taskId) {
            return axios
                .get('/search/get-task-info/?task_id=' + taskId)
                .then(response => {
                    return response.data['result'];
                });
        }
    },

    created() {
        // Перехватчик результата запроса для повторного запроса на статус и результат задачи.
        axios.interceptors.response.use(function (response) {
            if (response && response.data && response.data.state && response.data.state === 'PENDING') {
                return new Promise((resolve, reject) => {
                    setTimeout(() => {
                        resolve(axios.request(response.config));
                    }, 1000)
                });
            }
            return response;
        }, function (error) {
            return Promise.reject(error);
        });

        // Правило валидации для поискового запроса.
        this.$validator.extend('validQuery', {
            validate: (value, args) => {
                return new Promise((resolve, reject) => {
                    axios
                        .get('/search/validate-query/?search_type=' + this.searchType + '&value='
                            + value + '&param_type=' + args[0])
                        .then(response => {
                            return response.data['task_id'];
                        }).then(task_id => {
                        this.getTaskInfo(task_id).then(result => {
                            resolve(result);
                        });
                    });
                });
            }
        });
    },
}
