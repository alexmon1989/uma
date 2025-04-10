<template>
  <div class="g-pt-10--md">
    <input type="hidden"
           :name="'form-' + index + '-value'"
           :value="value">

    <label class="form-check-inline u-check g-pl-25">
      <input class="g-hidden-xs-up g-pos-abs g-top-0 g-left-0"
             type="checkbox"
             checked=""
             disabled=""
      >
      <div class="u-check-icon-checkbox-v4 g-absolute-centered--y g-left-0">
        <i class="fa" data-check-icon=""></i>
      </div><span v-html="translations.yes"></span>
    </label>
  </div>
</template>

<script>
import {translations} from "../../mixins/translations";

export default {
  name: "BooleanValue",
  props: {
    index: Number,
    ipcCode: [Object, Array],
    objType: Array,
    objState: Array,
    initialValue: [String, Array],
  },
  mixins: [translations],
  data() {
    return {
      value: ''
    }
  },
  mounted() {
    this.value = this.initialValue || this.ipcCode.default_value
  },
  watch: {
    ipcCode: function () {
      this.value = this.ipcCode.default_value
    }
  }
}
</script>

<style scoped>

</style>