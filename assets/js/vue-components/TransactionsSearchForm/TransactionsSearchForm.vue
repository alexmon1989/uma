<template>
    <form class="g-brd-around g-brd-gray-light-v4 g-pa-30 g-mb-30"
          @submit.prevent="handleSubmit">
        <h4 class="h6 g-font-weight-700 g-mb-20">{{ translations.startText }}:</h4>

        <!-- Об'єкт промислової власності -->
        <obj-type-input :obj-types="objTypes" v-model="obj_type"></obj-type-input>
        <!-- END Об'єкт промислової власності -->

        <!-- Об'єкт промислової власності -->
        <transactions-type-input :types="transactionTypes"
                                 ref="multiselect"
                                 v-model="transaction_type"></transactions-type-input>
        <!-- END Об'єкт промислової власності -->

        <!-- Дата сповіщення -->
        <date-input v-model="date"></date-input>
        <!-- END Дата сповіщення -->

        <!-- Дії -->
        <actions :is-form-submitting="isFormSubmitting"></actions>
        <!-- End Дії -->
    </form>
</template>

<script>
    import ObjTypeInput from "./ObjTypeInput.vue";
    import Actions from "./Actions.vue";
    import TransactionsTypeInput from "./TransactionsTypeInput.vue";
    import DateInput from "./DateInput.vue";
    import {translations} from "./mixins/translations";
    import axios from 'axios';

    export default {
        name: "TransactionsSearchForm",
        components: {ObjTypeInput, Actions, TransactionsTypeInput, DateInput},
        mixins: [translations],
        props: {
            initial: Object,
            langCode: String
        },
        data() {
            return {
                objTypes: [],
                obj_type: '',
                transaction_type: [],
                date: [],

                isFormSubmitting: false
            }
        },
        mounted() {
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

            document.onreadystatechange = () => {
                if (document.readyState === "complete") {
                    axios
                        .get('/' + this.langCode + '/search/get_obj_types_with_transactions/')
                        .then(response => {
                            return response.data['task_id'];
                        }).then(task_id => {
                            this.getTaskInfo(task_id).then(result => {
                                    this.objTypes = result;
                                    if (this.initial['obj_type']) {
                                        this.date = this.initial['date'][0].split(' ~ ');
                                        this.$nextTick(function () {
                                            this.obj_type = this.objTypes.find(e => e.id === parseInt(this.initial['obj_type'][0]));
                                            this.$nextTick(function () {
                                                this.transaction_type = this.initial['transaction_type'];
                                            });
                                        });
                                    }
                                }
                        );
                    });
                }
            }
        },
        methods: {
            handleSubmit: function () {
                this.isFormSubmitting = true;
                this.$validator.validate().then(valid => {
                    if (valid) {
                        document.forms[0].submit();
                    } else {
                        this.isFormSubmitting = false;
                    }
                });
            },

            // Получает статус и результат выполнения задачи
            getTaskInfo: function (taskId) {
                let siteKey = document.querySelector('meta[name="site-key"]').content;

                return grecaptcha.execute(siteKey, {action: 'gettransactiontypes'}).then(function (token) {
                    return axios
                        .get('/search/get-task-info/', {
                            params: {
                                task_id: taskId,
                                token: token,
                            }
                        })
                        .then(response => {
                            return response.data['result'];
                        });
                });
            }
        },
        computed: {
            transactionTypes: function () {
                if (this.obj_type && this.objTypes.length > 0) {
                    return this.objTypes.find(x => x.id === this.obj_type.id)['transactions_types'];
                } else {
                    return [];
                }
            }
        },
        watch: {
            transactionTypes: function (val, oldVal) {
                if (JSON.stringify(val) !== JSON.stringify(oldVal)) {
                    this.transaction_type = [];
                }
                if (val.length === 0) {
                    this.$refs.multiselect.deactivate();
                }
            }
        }
    }
</script>

<style scoped>

</style>