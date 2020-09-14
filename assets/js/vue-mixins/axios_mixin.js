import axios from 'axios';

export default {
    created() {
        // Перехватчик результата запроса для повторного запроса на статус и результат задачи.
        axios.interceptors.response.use(function (response) {
            let config = response.config;

            // If config does not exist or the retry option is not set, reject
            if (!config || !config.retry) return Promise.reject(response);

            // Set the variable for keeping track of the retry count
            config.__retryCount = config.__retryCount || 0;

            // Check if we've maxed out the total number of retries
            if (config.__retryCount >= config.retry) {
                // Reject
                return Promise.reject(err);
            }

            // Increase the retry count
            config.__retryCount += 1;

            // Create new promise to handle exponential backoff
            let backoff = new Promise(function (resolve) {
                setTimeout(function () {
                    resolve();
                }, config.retryDelay || 1);
            });

            if (response && response.data && response.data.state && response.data.state === 'PENDING') {
                // Return the promise in which recalls axios to retry the request
                return backoff.then(function () {
                    return axios(config);
                });
            }

            return response;
        }, function (error) {
            return Promise.reject(error);
        });
    }
}
