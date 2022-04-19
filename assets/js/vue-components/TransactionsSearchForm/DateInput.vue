<template>
    <div class="form-group g-mb-20"
         :class="{ 'u-has-error-v1': errors.has('date') }">
        <label for="date">{{ translations.transactionDate }}</label>

        <date-picker name="date"
                     id="date"
                     placeholder="Оберіть діапазон дат"
                     class="w-100 h-100 g-rounded-4 g-color-main g-color-primary--hover"
                     :value="value"
                     range
                     :lang="lang"
                     :first-day-of-week="1"
                     format="DD.MM.YYYY"
                     value-type="format"
                     v-validate="'required'"
                     confirm
                     :shortcuts="false"
                     v-on:confirm="onDateConfirm"
        ></date-picker>

        <small class="form-control-feedback" v-if="errors.has('date')">{{ translations.validationErrors[errors.firstRule('date')] }}</small>
    </div>
</template>

<script>
    import {translations} from "./mixins/translations";
    import DatePicker from 'vue2-datepicker';
    import datePickerMixin from './../../vue-mixins/date_picker_mixin.js';

    export default {
        name: "DateInput",
        components: {DatePicker},
        props: {
            initialData: [Array, String]
        },
        data() {
            return {
                lang: '',
                value: [],
            }
        },
        watch: {
            initialData: {
                immediate: true,
                handler(value) {
                    this.value = value
                }
            }
        },
        mounted() {
            this.lang = this.translations.transactionDateLang;
        },
        mixins: [translations, datePickerMixin],
        inject: ['$validator'],
    }
</script>

<style lang="scss">
    #date, .date-picker {
        .mx-input {
            height: 41px !important;
        }
    }

    .u-has-error-v1 {
        .mx-input {
            background-color: #fff0f0;
        }
    }
</style>