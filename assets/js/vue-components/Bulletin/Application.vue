<template>
    <v-card
            class="pt-6 mx-auto"
            flat
    >
        <div v-if="app_data">
            <h3 class="h4 g-mb-15">Дані заявки</h3>

            <v-row v-for="code in codes"
                   v-if="app_data[code].value"
                   class="text-left g-py-5"
                   tag="v-card-text"
            >
                <v-col v-if="app_data[code].value"
                       cols="12"
                       md="5"
                       class="mr-4 g-pa-5"
                       tag="strong"
                >{{ app_data[code].title }}:</v-col>
                <v-col v-if="app_data[code].value && code === 'code_540'"
                       class="g-pa-5"
                ><img :src="app_data[code].value" class="img-fluid"></v-col>
                <v-col v-else
                       class="g-pa-5"
                       v-html="app_data[code].value"
                ></v-col>
            </v-row>
        </div>
        <div v-else>Завантаження даних...</div>
    </v-card>
</template>

<script>
    import axios from 'axios';

    export default {
        name: "Application",

        props: ['app_number'],

        data: () => ({
            app_data: false,
            codes: [
                'code_210',
                'code_220',
                'code_230',
                'code_310',
                'code_320',
                'code_330',
                'code_441',
                'code_531',
                'code_540',
                'code_591',
                'code_731',
                'code_740',
                'code_750',
                'code_511',
            ]
        }),

        watch: {
            app_number: function (val) {
                this.getAppData(val)
            },
        },

        mounted() {
            this.getAppData(this.app_number);

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
        },

        methods: {
            getAppData: function (app_number) {
                this.app_data = false;
                axios
                    .get('/uk/bulletin/app-details-task/?app_number=' + app_number)
                    .then(response => {
                        return response.data['task_id'];
                    }).then(task_id => {
                            this.getTaskInfo(task_id).then(result => {
                                this.app_data = result;
                            }
                        );
                    });
            },

            // Получает статус и результат выполнения задачи
            getTaskInfo: function (taskId) {
                return axios
                    .get('/uk/bulletin/get-task-info/', {
                        params: {
                            task_id: taskId,
                        }
                    })
                    .then(response => {
                        return response.data['result'];
                    });
            }
        }
    }
</script>

<style scoped>

</style>