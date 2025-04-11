<template>
  <div>
    <input type="text"
           class="form-control form-control-md g-brd-gray-light-v3 g-rounded-4 g-px-14 g-pt-9 g-pb-8 g-min-height-40"
           :name="'form-' + index + '-value'"
           v-model="value"
           ref="value"
           @input="updateValue"
           @focus="onValueFocus"
           @blur="onValueBlur"
           :disabled="ipcCode.length === 0 || ipcCodesFiltered.length === 0"
           autocomplete="off"
           :placeholder="translations.value"
           data-vv-delay="500"
           v-validate="{
            required: true,
            validQuery: [ipcCode, objType, objState]
           }"
    >
    <small class="form-control-feedback"
           v-if="errors.has('form-' + index + '-value')"
    >{{ translations.validationErrors[errors.firstRule('form-' + index + '-value')] }}</small>

    <div class="d-flex justify-content-around g-pt-5"
         @focus="valueFocused = true">
      <button type="button"
              v-for="(operator, index) in logicalOperators"
              v-show="valueFocused && operator.dataTypes.includes(dataType)"
              ref="logical_operator"
              class="btn btn-xs btn-secondary"
              @click="onLogicalOperatorBtnClick(operator.value)"
      >{{ operator.value }}</button>
    </div>
  </div>
</template>

<script>
import {translations} from "../../mixins/translations";

export default {
  name: "TextValue",
  inject: ['$validator'],
  mixins: [translations],
  props: {
    index: Number,
    ipcCode: [Object, Array],
    objType: Array,
    objState: Array,
    ipcCodesFiltered: Array,
    initialValue: [String, Array],
    dataType: String
  },
  data: function () {
    return {
      value: this.initialValue,
      valueFocused: false,
      // Логические операторы. dataTypes определяет какие доступны для каких типов кодов ИНИД
      logicalOperators: [
        {
          'value': ' ' + gettext('ТА') + ' ',
          'dataTypes': ['date', 'integer', 'geography', 'varchar']
        },
        {
          'value': ' ' + gettext('АБО') + ' ',
          'dataTypes': ['date', 'integer', 'geography', 'varchar']
        },
        {
          'value': ' ' + gettext('НЕ') + ' ',
          'dataTypes': ['date', 'integer', 'geography', 'varchar']
        },
        {
          'value': '(',
          'dataTypes': ['date', 'integer', 'geography', 'varchar']
        },
        {
          'value': ')',
          'dataTypes': ['date', 'integer', 'geography', 'varchar']
        },
        {
          'value': '*',
          'dataTypes': ['geography', 'varchar']
        },
        {
          'value': '?',
          'dataTypes': ['geography', 'varchar']
        },
        {
          'value': '<',
          'dataTypes': ['date', 'integer']
        },
        {
          'value': '>',
          'dataTypes': ['date', 'integer']
        },
        {
          'value': '=',
          'dataTypes': ['date', 'integer']
        },
      ]
    }
  },
  methods: {
    updateValue: function (e) {
      this.$emit('updateValue', this.value)
    },

    onLogicalOperatorBtnClick: function (text) {
        const $value = $(this.$refs.value);
        const cursorPos = $value.prop('selectionStart');
        const v = $value.val();
        const textBefore = v.substring(0,  cursorPos);
        const textAfter  = v.substring(cursorPos, v.length);

        this.value = textBefore + text + textAfter;

        this.$nextTick(function () {
            this.$refs.value.focus();
            let newCursorPos = cursorPos + text.length;
            this.$refs.value.setSelectionRange(newCursorPos, newCursorPos);
        });
    },

    // Обработчик события потери фокуса поля "Значение".
    onValueBlur: function (e) {
        this.valueFocused = this.$refs.logical_operator.includes(e.relatedTarget);
        // Для срабатывания нажатия других кнопок
        if (!this.valueFocused && e.relatedTarget) {
            e.relatedTarget.click();
        }
    },

    // Обработчик приобретения фокуса полем "Значение".
    onValueFocus: function (e) {
        this.valueFocused = true;
    },
  },
  watch: {
    initialValue: function (val) {
      this.value = val
    }
  }
}
</script>

<style scoped>

</style>