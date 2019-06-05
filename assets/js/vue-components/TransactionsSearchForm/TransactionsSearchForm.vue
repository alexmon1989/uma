<template>
    <form class="g-brd-around g-brd-gray-light-v4 g-pa-30 g-mb-30"
          @submit.prevent="handleSubmit">
        <h4 class="h6 g-font-weight-700 g-mb-20">{{ translations.startText }}:</h4>

        <!-- Об'єкт промислової власності -->
        <obj-type-input :obj-types="objTypes" v-model="obj_type"></obj-type-input>
        <!-- END Об'єкт промислової власності -->

        <!-- Об'єкт промислової власності -->
        <transactions-type-input :types="transactionTypes" v-model="transaction_type"></transactions-type-input>
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

    export default {
        name: "TransactionsSearchForm",
        components: {ObjTypeInput, Actions, TransactionsTypeInput, DateInput},
        mixins: [translations],
        props: {
            objTypes: Array,
            initial: Object
        },
        data() {
            return {
                obj_type: '',
                transaction_type: [],
                date: [],

                isFormSubmitting: false
            }
        },
        mounted() {
            if (this.initial['obj_type']) {
                this.obj_type = this.initial['obj_type'][0].toString();
                this.date = this.initial['date'][0].split(' ~ ');
                this.$nextTick(function () {
                    this.transaction_type = this.initial['transaction_type'];
                });
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
            }
        },
        computed: {
            transactionTypes: function () {
                if (this.obj_type) {
                    return this.objTypes.find(x => x.id === parseInt(this.obj_type))['transactions_types'];
                } else {
                    return [];
                }
            }
        }
    }
</script>

<style scoped>

</style>