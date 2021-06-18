<template>
    <div class="form-group g-mb-20"
        :class="{ 'u-has-error-v1': errors.has('app_number') }">
        <label class="g-mb-10 g-font-weight-600" for="app_number">{{ translations.appNumberFieldLabel }}</label>
        <input v-model="value"
               @input="handleInput"
               id="app_number"
               class="form-control g-rounded-3 g-py-9 g-px-10 g-brd-gray-light-v3--focus"
               type="text"
               name="app_number"
               :disabled="!feeType"
               v-validate="{ required: feeType && feeType.needs_app_number, validApplication: feeType && feeType.needs_app_number }"
               data-vv-validate-on="blur"
               :placeholder="translations.appNumberFieldPlaceholder">
        <small class="form-control-feedback"
               v-if="errors.has('app_number')"
        >{{ translations.validationErrors[errors.firstRule('app_number')] }}</small>
    </div>
</template>

<script>
    import {translations} from "./mixins/translations";
    import validationMixin from './mixins/validation_mixin';

    export default {
        name: "AppNumber",
        props: ["group", "feeType"],
        inject: ['$validator'],
        mixins: [translations, validationMixin],
        data() {
            return {
                value: null,
            }
        },
        methods: {
            handleInput() {
                this.$emit('input', this.value)
            },
        }
    }
</script>

<style scoped>

</style>