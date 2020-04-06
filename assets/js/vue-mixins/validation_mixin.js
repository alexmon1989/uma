import axios from 'axios';

export default {
    methods: {
        // Получает статус и результат выполнения задачи
        getTaskInfo: function (taskId) {
            let siteKey = document.querySelector("meta[name='site-key']").getAttribute("content");

            return grecaptcha.execute(siteKey, {action: 'validation'}).then(function (token) {
                return axios
                    .get('/search/get-task-info/', {'params': {'task_id': taskId, 'token': token}})
                    .then(response => {
                        return response.data['result'];
                    });
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
                            + value + '&param_type=' + args.id;
                    } else {
                        validatePath = '/search/validate-query/?search_type=advanced&value='
                                            + value + '&ipc_code=' + args[0].id
                                            + '&obj_type=' + args[1].id
                                            + '&obj_state=' + args[2].map(a => a.id).join('&obj_state=')
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
