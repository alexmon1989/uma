<template>
    <div class="form-group g-mb-20"
        :class="{ 'u-has-error-v1': errors.has('group') }">
        <label class="g-mb-10 g-font-weight-600" for="group_id">{{ translations.groupFieldLabel }}</label>
        <multiselect v-model="value"
                     @input="handleInput"
                     :placeholder="translations.groupFieldPlaceholder"
                     :showLabels="false"
                     label="title"
                     track-by="id"
                     id="group_id"
                     name="group"
                     v-validate="'required'"
                     :allowEmpty="false"
                     :options="options"></multiselect>
        <small class="form-control-feedback"
               v-if="errors.has('group')"
        >{{ translations.validationErrors[errors.firstRule('group')] }}</small>
    </div>
</template>

<script>
    import {translations} from "./mixins/translations";

    export default {
        name: "GroupSelect",
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
        }
    }
</script>

<style scoped>

</style>