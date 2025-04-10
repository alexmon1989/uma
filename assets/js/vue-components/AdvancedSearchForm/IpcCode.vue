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
                    <value-field
                        :data-type="dataType"
                        :index="index"
                        :ipc-code="ipcCode"
                        :obj-state="objState"
                        :obj-type="objType"
                        :ipc-codes-filtered="ipcCodesFiltered"
                        :initial-value="value"
                        @updateValue="onUpdateValue"
                    ></value-field>
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
    import ValueField from './Fields/ValueField.vue'

    export default {
        name: "ipcCode",
        components: {ValueField, DatePicker},
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
            onUpdateValue: function (val) {
              this.value = val
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
            dataType(val, oldVal) {
                const isSpecialType = type => type === "date" || type === "boolean";

                if (oldVal && val !== oldVal && (isSpecialType(val) || isSpecialType(oldVal))) {
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