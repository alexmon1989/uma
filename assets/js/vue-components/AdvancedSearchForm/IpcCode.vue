<template>
    <div class="row">
        <div class="col-md-11">
            <div class="row d-flex align-items-start">
                <!-- Об'єкт промислової власності -->
                <div class="col-md-3 g-mb-15 g-pr-7--md"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-obj_type') }">

                    <select multiple="multiple"
                            :name="'form-' + index + '-obj_type'"
                            class="d-none">
                        <option v-for="option in objTypes" :value="option.id" :selected="objType.includes(option)"></option>
                    </select>

                    <multiselect v-model="objType"
                                 :options="objTypes"
                                 :placeholder="translations.objType"
                                 selectLabel=""
                                 deselectLabel="⨯"
                                 selectedLabel="✓"
                                 :multiple="true"
                                 v-validate="'required'"
                                 :searchable="false"
                                 label="value"
                                 track-by="id"
                                 :data-vv-name="'form-' + index + '-obj_type'"
                    ></multiselect>

                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-obj_type')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-obj_type')] }}</small>
                </div>
                <!-- END Об'єкт промислової власності -->

                <!-- Стан об'єкта -->
                <div class="col-md-3 g-mb-15 g-px-8--md"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-obj_state') }">

                    <select multiple="multiple"
                            :name="'form-' + index + '-obj_state'"
                            class="d-none">
                        <option v-for="option in objStates" :value="option.id" :selected="objState.includes(option)"></option>
                    </select>

                    <multiselect v-model="objState"
                                 :options="objStates"
                                 :placeholder="translations.objState"
                                 :disabled="objType.length > 0 && objType[0].id === 17"
                                 v-validate="{
                                    required: !wkmSelected
                                 }"
                                 selectLabel=""
                                 deselectLabel="⨯"
                                 selectedLabel="✓"
                                 :multiple="true"
                                 :searchable="false"
                                 label="value"
                                 track-by="id"
                                 :data-vv-name="'form-' + index + '-obj_state'">
                    </multiselect>

                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-obj_state')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-obj_state')] }}</small>
                </div>
                <!-- END Стан об'єкта -->

                <!-- Код ІНІД -->
                <div class="col-md-3 g-mb-15 g-px-8--md"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-ipc_code') }">

                    <select :name="'form-' + index + '-ipc_code'"
                            class="d-none">
                        <option v-for="option in ipcCodesFiltered" :value="option.id" :selected="option.id === ipcCode.id"></option>
                    </select>

                    <multiselect v-model="ipcCode"
                                 :options="ipcCodesFiltered"
                                 :placeholder="translations.ipcCode"
                                 :showLabels="false"
                                 label="value"
                                 track-by="id"
                                 :allowEmpty="false"
                                 :disabled="objType.length === 0 || (objState.length === 0 && !wkmSelected)"
                                 :data-vv-name="'form-' + index + '-ipc_code'"
                                 v-validate="'required'"
                                 ref="multiselect"
                    ></multiselect>

                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-ipc_code')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-ipc_code')] }}</small>
                </div>
                <!-- END Код ІНІД -->

                <!-- Значення -->
                <div class="col-md-3 g-px-8--md"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-value') }">
                    <div v-if="dataType !== 'date'">
                        <input type="text"
                               class="form-control form-control-md g-brd-gray-light-v3 g-rounded-4 g-px-14 g-pt-9 g-pb-8 g-min-height-40"
                               :name="'form-' + index + '-value'"
                               v-model="value"
                               ref="value"
                               @focus="onValueFocus"
                               @blur="onValueBlur"
                               :disabled="ipcCode.length === 0 || ipcCodesFiltered.length === 0"
                               autocomplete="off"
                               :placeholder="translations.value"
                               data-vv-delay="500"
                               v-validate="{
                                required: true,
                                validQuery: [ipcCode, objType, objState]
                           }">
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
                            >{{ operator.value }}
                            </button>
                        </div>
                    </div>
                    <div v-else>
                        <date-picker :input-name="'form-' + index + '-value'"
                             :name="'form-' + index + '-value'"
                             class="w-100 h-100 g-rounded-4 g-color-main g-color-primary--hover date-picker"
                             v-model="value"
                             ref="value"
                             range
                             :lang="lang"
                             :first-day-of-week="1"
                             format="DD.MM.YYYY"
                             value-type="format"
                             v-validate="{
                                  required: true,
                                  validQuery: [ipcCode, objType, objState]
                             }"
                             data-vv-delay="500"
                             placeholder="Оберіть діапазон дат"
                             confirm
                             :shortcuts="false"
                             v-on:confirm="onDateConfirm"
                        ></date-picker>
                        <small class="form-control-feedback"
                               v-if="errors.has('form-' + index + '-value')"
                        >{{ translations.validationErrors[errors.firstRule('form-' + index + '-value')] }}</small>
                    </div>
                </div>
                <!-- END Значення -->
            </div>
        </div>

        <div class="col-md-1 g-mb-30 g-mb-15--md g-pl-8--md">
            <button type="button"
                    class="btn btn-block btn-md u-btn-pink g-pt-10 g-pb-11 rounded-0"
                    @click="$emit('remove-ipc-group', index)"
                    :disabled="ipcGroupsCount === 1"
            ><i class="fa fa-minus"></i></button>
        </div>
    </div>
</template>

<script>
    import DatePicker from 'vue2-datepicker';
    import {translations} from "./mixins/translations";
    import datePickerMixin from './../../vue-mixins/date_picker_mixin.js';

    export default {
        name: "ipcCode",
        components: {DatePicker},
        inject: ['$validator'],
        mixins: [translations, datePickerMixin],
        props: {
            objTypes: Array,
            ipcCodes: Array,
            index: Number,
            ipcGroupsCount: Number,
            initialData: Object,
        },
        methods: {
            // Обработчик события нажатия на кнопку "Логический оператор".
            // Добавляет в позицию курсора значение логического оператора.
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
        mounted() {
            if (this.initialData['form-' + this.index + '-obj_type']) {
                this.objType = this.objTypes.filter(x => this.initialData['form-' + this.index + '-obj_type'].map(y => parseInt(y)).includes(x.id));
            }
            if (this.initialData['form-' + this.index + '-obj_state']) {
                this.objState = this.objStates.filter(x => this.initialData['form-' + this.index + '-obj_state'].map(y => parseInt(y)).includes(x.id));
            }
            this.$nextTick(function () {
                if (this.initialData['form-' + this.index + '-ipc_code']) {
                    this.ipcCode = this.ipcCodesFiltered.find(x => x.id === parseInt(this.initialData['form-' + this.index + '-ipc_code'][0]));

                    if (this.initialData['form-' + this.index + '-value']) {
                        if (this.dataType === "date") {
                            this.value = this.initialData['form-' + this.index + '-value'][0].split(' ~ ');
                        } else {
                            this.value = this.initialData['form-' + this.index + '-value'] || '';
                        }
                    }
                }
            });

            this.lang = this.translations.transactionDateLang;
        },
        data: function () {
            return {
                objStates: [
                    {'id': 1, 'value': gettext('Заявка')},
                    {'id': 2, 'value': gettext('Охоронний документ')},
                ], // состояния объектов охр. собств. 1 - заявка, 2 - охранный документ.
                objType: [], // выбранный объект пром. собств.
                objState: [], // выбранные состояния объектов пром. собств.
                ipcCode: [], // выбранный код ИНИД
                value: '', // введенное значение для поиска
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
                ],
                lang: 'en',
            }
        },
        computed: {
            // Тип данных выбранного поля ИНИД
            dataType: function () {
                if (!Array.isArray(this.ipcCode)) {
                    return this.ipcCodes.find(x => x.id === this.ipcCode.id).data_type;
                }
                return '';
            },

            ipcCodesFiltered: function () {
                // Фильтр по типам объектов пром. собств. и их состояниям.
                let ipcCodes = [];

                if (this.wkmSelected || (this.objType.length > 0 && this.objState.length > 0)) {
                    ipcCodes = this.ipcCodes
                        .filter(i => this.objType.every(j => i.obj_types.includes(j.id)))
                        .filter(i => this.objState.every(j => i.obj_states.includes(j.id)));
                }

                return ipcCodes;
            },

            wkmSelected: function () {
                return this.objType.length > 0 && this.objType[0].id === 17
            }
        },
        watch: {
            dataType: function (val, oldVal) {
                if (oldVal && val !== oldVal && (val === "date" || oldVal === "date")) {
                    this.value = '';
                }
            },

            ipcCodesFiltered: function (val, oldVal) {
                if (JSON.stringify(val) !== JSON.stringify(oldVal)) {
                    if (!Array.isArray(this.ipcCode)) {
                        this.ipcCode = [];
                    }
                }
                if (val.length === 0) {
                    this.$refs.multiselect.deactivate();
                }
            },

            objType: function (val, oldVal) {
              if (val.length && val[0].id === 17) {
                this.objState = []
              }
            }
        }
    }
</script>

<style lang="scss">
 .advanced-search-form {
   .multiselect {
     color: #555;
   }

   .multiselect__tags {
     border: 1px solid #ddd;
     border-radius: 4px;
   }

   .multiselect--disabled {
     background-color: inherit;
     opacity: 1;

     .multiselect__tags {
       background-color: #e9ecef;

       .multiselect__placeholder {
         color: #555;
         opacity: .5;
       }
     }

     .multiselect__select {
       background: #e9ecef;
       border-radius: 4px;
     }
   }

   .mx-input {
     border: 1px solid #ddd !important;
     max-height: 40px;
   }
 }
</style>