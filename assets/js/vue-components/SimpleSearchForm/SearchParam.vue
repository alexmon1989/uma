<template>
    <div class="row g-mb-5">
        <!-- Параметр пошуку -->
        <div class="col-md-5 g-pr-7--md">
            <div class="form-group g-mb-15"
                 :class="{ 'u-has-error-v1': errors.has('form-' + index + '-param_type') }">
                <chosen-select
                        class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                        :name="'form-' + index + '-param_type'"
                        v-validate="'required'"
                        v-model="paramType"
                        :data-placeholder="translations.selectParameter">
                    <option></option>
                    <option v-for="(type, key) in searchParameterTypes"
                            :key="key"
                            class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                            :value="type.id">{{ type.field_label }}
                    </option>
                </chosen-select>
                <small class="form-control-feedback" v-if="errors.has('form-' + index + '-param_type')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-param_type')] }}</small>
            </div>
        </div>
        <!-- End Параметр пошуку -->

        <!-- Значення параметра пошуку -->
        <div class="col-md-6 g-px-8--md">
            <div class="form-group g-mb-20"
                 :class="{ 'u-has-error-v1': errors.has('form-' + index + '-value') }">
                <date-picker :input-name="'form-' + index + '-value'"
                             :name="'form-' + index + '-value'"
                             class="w-100 h-100 g-rounded-4 g-color-main g-color-primary--hover date-picker"
                             v-model="value"
                             range
                             :lang="lang"
                             :first-day-of-week="1"
                             format="DD.MM.YYYY"
                             value-type="format"
                             v-validate="{
                                  required: true,
                                  validQuery: paramType
                             }"
                             placeholder="Оберіть діапазон дат"
                             confirm
                             :shortcuts="false"
                             v-if="type === 'date'"
                ></date-picker>
                <input class="form-control form-control-md g-brd-gray-light-v7 g-brd-gray-light-v3--focus g-rounded-4 g-px-14 g-pt-10 g-pb-11"
                       type="text"
                       autocomplete="off"
                       :name="'form-' + index + '-value'"
                       v-validate="{
                            required: true,
                            validQuery: paramType
                       }"
                       data-vv-delay="500"
                       v-model="value"
                       :placeholder="translations.value"
                       v-else>
                <small class="form-control-feedback" v-if="errors.has('form-' + index + '-value')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-value')] }}</small>
            </div>
        </div>
        <!-- End Значення параметра пошуку -->

        <div class="col-md-1 g-mb-30 g-mb-15--md g-pl-8--md">
            <button type="button"
                    class="btn btn-block btn-md u-btn-pink g-pt-10 g-pb-11 rounded-0"
                    @click="$emit('remove-search-parameter', index)"
                    :disabled="searchParametersCount === 1"
            ><i class="fa fa-minus"></i></button>
        </div>
    </div>
</template>

<script>
    import ChosenSelect from "../ChosenSelect.vue";
    import DatePicker from 'vue2-datepicker';
    import {translations} from "./mixins/translations";

    export default {
        name: "SearchParam",
        mixins: [translations],
        components: {ChosenSelect, DatePicker},
        inject: ['$validator'],
        props: {
            searchParameterTypes: Array,
            index: Number,
            searchParametersCount: Number,
            initialData: Object,
        },
        data() {
            return {
                paramType: '',
                value: '',
                lang: 'en',
            }
        },
        computed: {
            // Тип параметра (text, date, integer, keyword)
            type() {
                let self = this;
                let element = this.searchParameterTypes.find(function (el) {
                     return el.id === parseInt(self.paramType);
                });
                if (element) {
                    return element.field_type;
                }
                return '';
            }
        },
        mounted() {
            if (this.initialData['form-' + this.index + '-param_type']) {
                this.paramType = this.initialData['form-' + this.index + '-param_type'];
            }

            if (this.initialData['form-' + this.index + '-value']) {
                if (this.type === "date") {
                    this.value = this.initialData['form-' + this.index + '-value'][0].split(' ~ ');
                } else {
                    this.value = this.initialData['form-' + this.index + '-value'] || '';
                }
            }

            this.lang = this.translations.transactionDateLang;
        },
        watch: {
            type: function (val, oldVal) {
                if (oldVal && val !== oldVal && (val === "date" || oldVal === "date")) {
                    this.value = '';
                }
            }
        }
    }
</script>

<style lang="scss">
    .mx-datepicker-btn-confirm {
        color: #037fe2 !important;
        border-color: #037fe2 !important;
    }

    .mx-datepicker-btn-confirm:hover {
        color: lighten(#037fe2, 20%) !important;
        border-color: lighten(#037fe2, 20%) !important;
    }
</style>