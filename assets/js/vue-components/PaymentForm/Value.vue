<template>
    <div class="form-group g-mb-20"
        :class="{ 'u-has-error-v1': errors.has('value') }">
        <label class="g-mb-10 g-font-weight-600" for="value">{{ translations.valueFieldLabel }}</label>
        <input v-model="value"
               @input="handleInput"
               id="value"
               class="form-control g-rounded-3 g-py-9 g-px-10 g-brd-gray-light-v3--focus"
               type="text"
               v-validate="'required|integer'"
               name="value"
               autocomplete="off"
               :placeholder="translations.valueFieldPlaceholder">
        <small class="form-control-feedback" v-if="errors.has('value')">{{ translations.validationErrors[errors.firstRule('value')] }}</small>
    </div>
</template>

<script>
    import {translations} from "./mixins/translations";

    export default {
        name: "Value",
        inject: ['$validator'],
        mixins: [translations],
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