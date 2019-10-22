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
                    let validatePath = '';

                    // Если на вход попался массив дат
                    if (typeof value === 'object' && value.length === 2) {
                        if (value[0] && value[1]) {
                            value = value[0] + ' ~ ' + value[1];
                        } else {
                            value = '';
                        }
                    }

                    if (this.searchType === 'simple') {
                        validatePath = '/search/validate-query/?search_type=simple&value='
                            + value + '&param_type=' + args[0];
                    } else {
                        validatePath = '/search/validate-query/?search_type=advanced&value='
                                            + value + '&ipc_code=' + args[0]
                                            + '&obj_type=' + args[1]
                                            + '&obj_state=' + args[2].join('&obj_state=')
                    }
                    axios
                        .get(validatePath)
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
    }
}
