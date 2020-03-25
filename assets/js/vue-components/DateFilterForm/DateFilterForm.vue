<template>
    <form class="form-inline g-brd-around g-brd-gray-light-v4 g-pa-15 g-mb-15"
          @submit.prevent="handleSubmit">

        <div class="form-group"
             :class="{'u-has-error-v1': errors.has('date_range')}">
            <label for="date_range" class="g-font-weight-600">{{ translations.label }}:</label>

            <div class="g-px-15--sm g-py-10">
                <date-picker input-name="date_range"
                             name="date_range"
                             id="date_range"
                             v-model="value"
                             class="g-color-main g-color-primary--hover date-picker border-0 g-width-300"
                             range
                             :lang="lang"
                             :first-day-of-week="1"
                             format="DD.MM.YYYY"
                             value-type="format"
                             v-validate="{
                                  required: true
                             }"
                             placeholder="Оберіть діапазон дат"
                             confirm
                             :shortcuts="false"
                             v-on:confirm="onDateConfirm"
                ></date-picker>
                <small class="form-control-feedback"
                       v-if="errors.has('date_range')"
                >{{ translations.validationErrors[errors.firstRule('date_range')] }}</small>
            </div>
        </div>

        <button type="submit"
                class="btn btn-md u-btn-indigo rounded-0"
                :disabled="!value[0] && !value[1]"><i class="fa fa-filter g-mr-5"></i>{{ translations.filter }}</button>
    </form>
</template>

<script>
    import {translations} from "./mixins/translations";
    import datePickerMixin from './../../vue-mixins/date_picker_mixin.js';
    import DatePicker from 'vue2-datepicker';

    export default {
        name: "DateFilterForm",
        props: ['initialDateRange'],
        mixins: [translations, datePickerMixin],
        components: {DatePicker},
        data: function () {
            return {
                value: '',
                lang: 'en'
            }
        },
        mounted() {
            this.lang = this.translations.transactionDateLang;
            this.value = this.initialDateRange.split(' ~ ');
        },
        methods: {
            handleSubmit() {
                if (!this.value[0] && !this.value[1]) {
                    this.value = '';
                }
                this.$validator.validate().then(valid => {
                    if (valid) {
                        document.forms[0].submit();
                    }
                });
            }
        }
    }
</script>

<style scoped>

</style>