<template>
    <div class="form-group g-mb-20"
        :class="{ 'u-has-error-v1': errors.has('fee_type') }">
        <label class="g-mb-10 g-font-weight-600" for="fee_type_id">{{ translations.feeTypeFieldLabel }}</label>
        <multiselect v-model="value"
                     @input="handleInput"
                     :placeholder="translations.feeTypeFieldPlaceholder"
                     :showLabels="false"
                     label="title"
                     track-by="id"
                     id="fee_type_id"
                     name="fee_type"
                     v-validate="'required'"
                     :allowEmpty="false"
                     :disabled="options.length === 0"
                     :options="options"></multiselect>
        <small class="form-control-feedback"
               v-if="errors.has('fee_type')"
        >{{ translations.validationErrors[errors.firstRule('fee_type')] }}</small>
    </div>
</template>

<script>
    import {translations} from "./mixins/translations";

    export default {
        name: "FeeTypeSelect",
        props: ['options'],
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
        },
        watch: {
            options() {
              this.value = null;
              this.handleInput();
            },
        }
    }
</script>

<style scoped>

</style>