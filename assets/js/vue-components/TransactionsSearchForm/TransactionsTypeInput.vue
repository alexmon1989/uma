<template>
    <div class="form-group g-mb-20"
         :class="{ 'u-has-error-v1': errors.has('transaction_type') }">
        <label for="transaction_type">{{ translations.transactionType }}</label>
        <chosen-select
                class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                :data-placeholder="translations.transactionType"
                :disabled="types.length === 0"
                name="transaction_type"
                :value="value"
                multiple
                @input="$emit('input', $event)"
                v-validate="'required'"
                id="transaction_type"
                ref="transaction_type"
        >
            <option v-for="type in types"
                    class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                    :value="type"
                    :key="type"
            >{{ type.charAt(0).toUpperCase() + type.slice(1) }}</option>
        </chosen-select>
        <small class="form-control-feedback" v-if="errors.has('transaction_type')">{{ translations.validationErrors[errors.firstRule('transaction_type')] }}</small>
    </div>
</template>

<script>
    import ChosenSelect from "../ChosenSelect.vue";
    import {translations} from "./mixins/translations";

    export default {
        name: "TransactionsTypeInput",
        components: {ChosenSelect},
        mixins: [translations],
        inject: ['$validator'],
        props: {
            types: Array,
            value: [Number, String, Array],
        },
        watch: {
            types: function (val) {
                this.$nextTick(function () {
                    $(this.$refs.transaction_type.$el).trigger('chosen:updated');
                });
            }
        }
    }
</script>

<style lang="scss">

    #transaction_type_chosen.chosen-disabled {
        .chosen-choices {
            background-color: #e9ecef;
        }
    }

</style>