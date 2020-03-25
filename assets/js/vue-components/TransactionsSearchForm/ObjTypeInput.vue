<template>
    <div class="form-group g-mb-20"
         :class="{ 'u-has-error-v1': errors.has('obj_type') }">
        <label for="objType">{{ translations.objType }}</label>

        <select name="obj_type"
                class="d-none">
            <option v-for="option in objTypes" :value="option.id" :selected="value.id === option.id"></option>
        </select>

        <multiselect :value="value"
                     :options="objTypes"
                     :placeholder="translations.objType"
                     :showLabels="false"
                     :allowEmpty="false"
                     label="value"
                     track-by="id"
                     data-vv-name="obj_type"
                     v-validate="'required'"
                     @input="$emit('input', $event)"
                    id="objType"
        ></multiselect>
        <small class="form-control-feedback" v-if="errors.has('obj_type')">{{ translations.validationErrors[errors.firstRule('obj_type')] }}</small>
    </div>
</template>

<script>
    import {translations} from "./mixins/translations";

    export default {
        name: "ObjTypeInput",
        mixins: [translations],
        inject: ['$validator'],
        props: {
            objTypes: Array,
            value: [String, Object],
        }
    }
</script>

<style scoped>

</style>