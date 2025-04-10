<template>
  <div v-if="!dataType || dataType === 'varchar' || dataType === 'integer'">
    <text-value
        :index="index"
        :ipc-code="ipcCode"
        :obj-state="objState"
        :obj-type="objType"
        :ipc-codes-filtered="ipcCodesFiltered"
        :initial-value="initialValue"
    ></text-value>
  </div>

  <div v-else-if="dataType === 'date'">
    <date-value
        :index="index"
        :ipc-code="ipcCode"
        :obj-state="objState"
        :obj-type="objType"
        :initial-value="initialValue"
    ></date-value>
  </div>

  <div v-else-if="dataType === 'boolean'">
    <boolean-value
        :index="index"
        :ipc-code="ipcCode"
        :obj-state="objState"
        :obj-type="objType"
        :initial-value="initialValue"
    ></boolean-value>
  </div>
</template>

<script>
import TextValue from "./Value/TextValue.vue";
import DateValue from "./Value/DateValue.vue";
import BooleanValue from "./Value/BooleanValue.vue";
import {translations} from "../mixins/translations";
import datePickerMixin from '../../../vue-mixins/date_picker_mixin.js';

export default {
  name: "ValueField",
  inject: ['$validator'],
  components: {BooleanValue, DateValue, TextValue},
  mixins: [translations, datePickerMixin],
  props: {
    dataType: String,
    index: Number,
    ipcCode: [Object, Array],
    objType: Array,
    objState: Array,
    ipcCodesFiltered: Array,
    initialValue: [String, Array]
  }
}
</script>

<style scoped>

</style>