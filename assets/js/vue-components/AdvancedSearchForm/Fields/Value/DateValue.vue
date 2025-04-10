<template>
  <div>
    <date-picker :input-name="'form-' + index + '-value'"
                 :name="'form-' + index + '-value'"
                 class="w-100 h-100 g-rounded-4 g-color-main g-color-primary--hover date-picker"
                 v-model="value"
                 ref="value"
                 range
                 :lang="langSettings"
                 :first-day-of-week="1"
                 format="DD.MM.YYYY"
                 value-type="format"
                 v-validate="{
                   required: true,
                   validQuery: [ipcCode, objType, objState]
                 }"
                 data-vv-delay="500"
                 :placeholder="translations.valueDate"
                 confirm
                 :shortcuts="false"
                 v-on:confirm="onDateConfirm"
    ></date-picker>
    <small class="form-control-feedback"
           v-if="errors.has('form-' + index + '-value')"
    >{{ translations.validationErrors[errors.firstRule('form-' + index + '-value')] }}</small>
  </div>
</template>

<script>
import {translations} from "../../mixins/translations";
import DatePicker from "vue2-datepicker";
import datePickerMixin from '../../../../vue-mixins/date_picker_mixin.js';

export default {
  name: "DateValue",
  mixins: [translations, datePickerMixin],
  components: {DatePicker},
  inject: ['$validator'],
  props: {
    index: Number,
    ipcCode: [Object, Array],
    objType: Array,
    objState: Array,
    initialValue: [String, Array],
  },
  data: function () {
    return {
      value: this.initialValue,
      langSettings: {},
    }
  },
  watch: {
    initialValue: function (val) {
      this.value = val
    }
  },
  mounted() {
      this.langSettings = this.translations.transactionDateLang;
  }
}
</script>

<style scoped>

</style>