<template>
    <div class="g-brd-around g-brd-gray-light-v4 g-pa-30 g-mb-30">
        <group-select :options="groups"
                      v-model="group"
                      @input="handleGroupInput"></group-select>

        <fee-type-select :options="feeTypes"
                         v-model="feeType"></fee-type-select>

        <app-number :group="group" v-model="appNumber"></app-number>

        <value v-model="value"></value>

        <button type="button"
                class="btn btn-md u-btn-indigo rounded-0"
                @click="handleSubmit()"
                :disabled="isProcessing"
        >{{ translations.btnText }}</button>
    </div>
</template>

<script>
    import axios from 'axios';
    import GroupSelect from "./GroupSelect.vue";
    import FeeTypeSelect from "./FeeTypeSelect.vue";
    import AppNumber from "./AppNumber.vue";
    import Value from "./Value.vue";
    import {translations} from "./mixins/translations";

    export default {
        name: "PaymentForm",
        mixins: [translations],
        components: {
            GroupSelect,
            FeeTypeSelect,
            AppNumber,
            Value,
        },
        data() {
            return {
                groups: [],
                feeTypes: [],

                group: null,
                appNumber: null,
                feeType: null,
                value: null,

                error: null,

                isProcessing: false,
            }
        },
        methods: {
            getGroups() {
                axios
                    .get('/payments/api/groups/')
                    .then(response => {
                        this.groups = response['data'];
                    }).catch(error => {
                        this.error = error
                    });
            },

            getFeeTypes(groupId) {
                this.feeTypes = [];
                axios
                    .get('/payments/api/fee-types/' + groupId + '/')
                    .then(response => {
                        this.feeTypes = response['data'];
                    }).catch(error => {
                    this.error = error
                });
            },

            handleGroupInput(group) {
                this.getFeeTypes(group.id);
            },

            // Обработчик отправки формы
            handleSubmit: function () {
                this.isProcessing = true;
                this.$validator.validate().then(valid => {
                    // Запрос на создание заказа на оплату
                    if (valid) {
                        axios
                            .post('/payments/api/orders', {
                                'value': this.value,
                                'app_number': this.appNumber,
                                'fee_type': this.feeType.id,
                            })
                            .then(response => {
                                this.isProcessing = false;
                                // Переадресация на страницу заказа со ссылкой перехода на оплату
                                window.location = '/payments/order/' + response.data.id + '/'
                            }).catch(error => {
                                this.error = error;
                                this.isProcessing = false;
                            });
                    }
                });
            }
        },
        mounted() {
            this.getGroups();
        }
    }
</script>

<style scoped>

</style>