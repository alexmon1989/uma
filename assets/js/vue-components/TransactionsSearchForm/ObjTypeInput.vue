<template>
    <div class="form-group g-mb-20"
         :class="{ 'u-has-error-v1': errors.has('obj_type') }">
        <label for="objType">{{ translations.objType }}</label>
        <chosen-select
                class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                :data-placeholder="translations.objType"
                name="obj_type"
                :value="value"
                @input="$emit('input', $event)"
                v-validate="'required'"
                id="objType"
        >
            <option value=""></option>
            <option v-for="objType in objTypes"
                    class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                    :value="objType.id"
                    :key="objType.id"
            >{{ objType.value }}
            </option>
        </chosen-select>
        <small class="form-control-feedback" v-if="errors.has('obj_type')">{{ translations.validationErrors[errors.firstRule('obj_type')] }}</small>
    </div>
</template>

<script>
    import ChosenSelect from "../ChosenSelect.vue";
    import {translations} from "./mixins/translations";

    export default {
        name: "ObjTypeInput",
        components: {ChosenSelect},
        mixins: [translations],
        inject: ['$validator'],
        props: {
            objTypes: Array,
            value: [Number, String],
        },
        watch: {
            objTypes: function (val) {
                this.$nextTick(function () {
                    $("#objType").trigger('chosen:updated');
                });
            }
        }
    }
</script>

<style scoped>

</style>