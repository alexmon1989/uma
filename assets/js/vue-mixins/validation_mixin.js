import axios from 'axios';

export default {
    methods: {
        // Получает статус и результат выполнения задачи
        getTaskInfo: function (taskId) {
            return axios
                .get('/search/get-validation-info/', {'params': {'task_id': taskId}, retry: 4, retryDelay: 1000})
                .then(response => {
                    if (response.data['state'] === 'PENDING') {
                        // Если здесь state всё ещё PENDING, то это значит что сервер так и не провалидировал запрос,
                        // возвращается признак корректности запроса
                        return true;
                    }
                    return response.data['result'];
                });
        }
    },

    created() {
        // Перехватчик результата запроса для повторного запроса на статус и результат задачи.
        axios.interceptors.response.use(function (response) {
            let config = response.config;

            // If config does not exist or the retry option is not set, reject
            if(!config || !config.retry) return Promise.reject(response);

            // Set the variable for keeping track of the retry count
            config.__retryCount = config.__retryCount || 0;

            // Check if we've maxed out the total number of retries
            if (config.__retryCount >= config.retry) {
                // Reject
                return response;
            }

            // Increase the retry count
            config.__retryCount += 1;

            // Create new promise to handle exponential backoff
            let backoff = new Promise(function(resolve) {
                setTimeout(function() {
                    resolve();
                }, config.retryDelay || 1);
            });

            if (response && response.data && response.data.state && response.data.state === 'PENDING') {
                // Return the promise in which recalls axios to retry the request
                return backoff.then(function() {
                    return axios(config);
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
                    value = encodeURIComponent(value);

                    if (this.searchType === 'simple') {
                        validatePath = '/search/validate-query/?search_type=simple&value='
                            + value + '&param_type=' + args.id;

                    } else {
                        validatePath = '/search/validate-query/?search_type=advanced&value='
                                            + value + '&ipc_code=' + args[0].id
                                            + '&obj_type=' + args[1].map(a => a.id).join('&obj_type=')
                                            + '&obj_state=' + args[2].map(a => a.id).join('&obj_state=')
                    }
                    axios
                        .get(validatePath, {retry: 1})
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
