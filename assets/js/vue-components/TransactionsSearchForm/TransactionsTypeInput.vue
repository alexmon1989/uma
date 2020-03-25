<template>
    <div class="form-group g-mb-20"
         :class="{ 'u-has-error-v1': errors.has('transaction_type') }">
        <label for="transaction_type">{{ translations.transactionType }}</label>

        <select multiple="multiple"
                name="transaction_type"
                class="d-none">
            <option v-for="option in types" :value="option" :selected="value.includes(option)"></option>
        </select>

        <multiselect :value="value"
                     :disabled="types.length === 0"
                     @input="$emit('input', $event)"
                     :options="types"
                     :placeholder="translations.transactionType"
                     selectLabel=""
                     deselectLabel="⨯"
                     selectedLabel="✓"
                     :multiple="true"
                     v-validate="'required'"
                     :searchable="true"
                     data-vv-name="transaction_type"
                     id="transaction_type">
            <template slot="option" slot-scope="props">
                {{ props.option.charAt(0).toUpperCase() + props.option.slice(1) }}
            </template>
        </multiselect>
        <small class="form-control-feedback" v-if="errors.has('transaction_type')">{{ translations.validationErrors[errors.firstRule('transaction_type')] }}</small>
    </div>
</template>

<script>
    import {translations} from "./mixins/translations";

    export default {
        name: "TransactionsTypeInput",
        mixins: [translations],
        inject: ['$validator'],
        props: {
            types: Array,
            value: [Object, Array],
        }
    }
</script>

<style lang="scss">

</style>