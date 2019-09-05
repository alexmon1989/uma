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
                <input class="form-control form-control-md g-brd-gray-light-v7 g-brd-gray-light-v3--focus g-rounded-4 g-px-14 g-pt-10 g-pb-11"
                       type="text"
                       :autocomplete="autocomplete"
                       @focus="autocomplete = 'off'"
                       @blur="autocomplete = 'on'"
                       :name="'form-' + index + '-value'"
                       v-validate="{
                            required: true,
                            validQuery: paramType
                       }"
                       data-vv-delay="500"
                       v-model="value"
                       :placeholder="translations.value">
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

    export default {
        name: "SearchParam",
        components: {ChosenSelect},
        inject: ['$validator'],
        props: {
            searchParameterTypes: Array,
            index: Number,
            searchParametersCount: Number,
            initialData: Object,
        },
        data() {
            return {
                translations: {
                    selectParameter: gettext('Оберіть параметр пошуку'),
                    value: gettext('Значення'),
                    addBtnText: gettext('Додати параметр'),
                    validationErrors: {
                        required: gettext('Обов\'язкове поле для заповнення'),
                        validQuery: gettext('Поле містить невірне значення'),
                    },
                },
                paramType: '',
                value: '',
                autocomplete: 'on'
            }
        },
        mounted() {
            if (this.initialData['form-' + this.index + '-param_type']) {
                this.paramType = this.initialData['form-' + this.index + '-param_type'];
            }

            if (this.initialData['form-' + this.index + '-value']) {
                this.value = this.initialData['form-' + this.index + '-value'] || '';
            }
        }
    }
</script>

<style scoped>

</style>