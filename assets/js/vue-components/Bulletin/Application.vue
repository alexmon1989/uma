<template>
    <v-card
            class="pt-6 mx-auto text-center"
            flat
    >
        <transition name="application-fade" mode="out-in">
            <div v-if="app_data" key="data">
                <h3 class="h4 g-mb-15">Дані заявки</h3>

                <v-row v-for="code in codes"
                       :key="code"
                       v-if="app_data[code] && app_data[code].value"
                       class="text-left g-py-5"
                       tag="v-card-text"
                >
                    <v-col v-if="app_data[code].value"
                           cols="12"
                           md="5"
                           class="mr-4 g-pa-5"
                           tag="strong"
                    >{{ app_data[code].title }}:</v-col>
                    <v-col v-if="app_data[code].value && code === 'code_540' && app_data[code].type === 'image'"
                           class="g-pa-5"
                    >
                      <div class="g-mb-10" v-if="app_data['code_540_MULTIMEDIA_FILE']">
                        <video style="height: auto; width: auto; max-width: 250px;"
                               width="250px"
                               height="250px"
                               controls="controls">
                          <source :src="app_data['code_540_MULTIMEDIA_FILE'].value">
                        </video>
                      </div>
                      <div class="g-mb-10" v-if="app_data['code_540_MULTIMEDIA_MADRID_LINK']">
                        <a :href="app_data['code_540_MULTIMEDIA_MADRID_LINK'].value"
                           target="_blank">{{ app_data['code_540_MULTIMEDIA_MADRID_LINK'].value }}</a>
                      </div>
                      <img :src="app_data[code].value" class="img-fluid" alt="">
                    </v-col>
                    <v-col v-else-if="app_data[code].value && code === 'code_9441'"
                           class="g-pa-5"
                    ><a :href="app_data[code].value"
                        target="_blank"><i class="fa fa-external-link g-mr-5"></i>Відкрити</a></v-col>
                    <v-col v-else
                           class="g-pa-5"
                           v-html="app_data[code].value"
                    ></v-col>
                </v-row>
            </div>
            <div class="d-flex justify-content-center g-mt-10" key="loading" v-else>
                <p class="text-danger" v-if="error">Помилка при отриманні даних. Спробуйте пізніше.</p>

                <v-progress-circular color="primary" indeterminate size="80" v-else></v-progress-circular>
            </div>
        </transition>
    </v-card>
</template>

<script>
    import axios from 'axios';
    import axiosMixin from './../../vue-mixins/axios_mixin.js';

    export default {
        name: "Application",

        props: ['app_number'],

        mixins: [axiosMixin],

        data: () => ({
            app_data: false,
            error: false,
            codes: [
                'code_111',
                'code_151',
                'code_190',
                'code_210',
                'code_220',
                'code_230',
                'code_310',
                'code_320',
                'code_330',
                'code_441',
                'code_450',
                'code_531',
                'code_891',
                'code_539_i',
                'code_540',
                'code_553',
                'code_571',
                'code_4551',
                'code_529',
                'code_539',
                'code_4573',
                'code_591',
                'code_731',
                'code_740',
                'code_750',
                'code_511',
                'code_9441',
            ]
        }),

        watch: {
            app_number: function (val) {
                this.getAppData(val)
            },
        },

        mounted() {
            this.getAppData(this.app_number);
        },

        methods: {
            getAppData: function (app_number) {
                this.app_data = false;
                this.error = false;
                axios
                    .get('/uk/bulletin/app-details-task/?app_number=' + app_number, {retry: 1})
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
                    .get('/uk/bulletin/get-task-info/', {'params': {'task_id': taskId}, retry: 10, retryDelay: 1000})
                    .then(response => {
                        return response.data['result'];
                    }).catch(() => {
                        this.error = true;
                    });
            }
        }
    }
</script>

<style scoped>
    .application-fade-enter-active, .application-fade-leave-active {
      transition: opacity .3s;
    }
    .application-fade-enter, .application-fade-leave-to {
      opacity: 0;
    }
</style>