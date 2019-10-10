<template>
    <div class="row">
        <div class="col-md-11">
            <div class="row d-flex align-items-start">
                <!-- Об'єкт промислової власності -->
                <div class="col-md-3 g-mb-15 g-pr-7--md"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-obj_type') }">
                    <chosen-select
                            class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                            :data-placeholder="translations.objType"
                            :name="'form-' + index + '-obj_type'"
                            v-model="objType"
                            v-validate="'required'"
                    >
                        <option value=""></option>
                        <option v-for="objType in objTypes"
                                class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                :value="objType.id"
                                :key="objType.id"
                        >{{ objType.value }}
                        </option>
                    </chosen-select>
                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-obj_type')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-obj_type')] }}</small>
                </div>
                <!-- END Об'єкт промислової власності -->

                <!-- Стан об'єкта -->
                <div class="col-md-3 g-mb-15 g-px-8--md"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-obj_state') }">
                    <chosen-select
                            class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                            :data-placeholder="translations.objState"
                            multiple
                            :name="'form-' + index + '-obj_state'"
                            v-model="objState"
                            v-validate="'required'"
                    >
                        <option v-for="objState in objStates"
                                class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                :value="objState.id"
                                :key="objState.id"
                        >{{ objState.value }}
                        </option>
                    </chosen-select>
                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-obj_state')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-obj_state')] }}</small>
                </div>
                <!-- END Стан об'єкта -->

                <!-- Код ІНІД -->
                <div class="col-md-3 g-mb-15 g-px-8--md"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-ipc_code') }">
                    <chosen-select
                            ref="ipc_code"
                            class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                            :data-placeholder="translations.ipcCode"
                            id="obj_status"
                            :name="'form-' + index + '-ipc_code'"
                            v-model="ipcCode"
                            :disabled="objType === '' || objState.length === 0"
                            v-validate="'required'"
                    >
                        <option value=""></option>
                        <option v-for="ipcCode in ipcCodesFiltered"
                                class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                :value="ipcCode.id"
                                :key="ipcCode.id"
                        >{{ ipcCode.value }}
                        </option>
                    </chosen-select>
                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-ipc_code')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-ipc_code')] }}</small>
                </div>
                <!-- END Код ІНІД -->

                <!-- Значення -->
                <div class="col-md-3 g-px-8--md"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-value') }">
                    <input type="text"
                           class="form-control form-control-md g-brd-gray-light-v3--focus g-rounded-4 g-px-14 g-py-9"
                           :name="'form-' + index + '-value'"
                           v-model="value"
                           ref="value"
                           @focus="onValueFocus"
                           @blur="onValueBlur"
                           :disabled="ipcCode === '' || ipcCodesFiltered.length === 0"
                           autocomplete="off"
                           :placeholder="translations.value"
                           v-validate="{
                                required: true,
                                validQuery: [ipcCode, objType, objState]
                           }">
                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-value')">{{ translations.validationErrors[errors.firstRule('form-' + index + '-value')] }}</small>

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
    import ChosenSelect from "../ChosenSelect.vue";

    export default {
        name: "ipcCode",
        components: {ChosenSelect},
        inject: ['$validator'],
        props: {
            objTypes: Array,
            objStates: Array,
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
            }
        },
        mounted() {
            if (this.initialData['form-' + this.index + '-obj_type']) {
                this.objType = this.initialData['form-' + this.index + '-obj_type'];
            }
            if (this.initialData['form-' + this.index + '-obj_state']) {
                this.objState = this.initialData['form-' + this.index + '-obj_state'];
            }
            this.$nextTick(function () {
                if (this.initialData['form-' + this.index + '-ipc_code']) {
                    this.ipcCode = this.initialData['form-' + this.index + '-ipc_code'];
                }
            });
            if (this.initialData['form-' + this.index + '-value']) {
                this.value = this.initialData['form-' + this.index + '-value'];
            }
        },
        data: function () {
            return {
                objType: '', // выбранный объект пром. собств.
                objState: [], // выбранные состояния объектов пром. собств.
                ipcCode: '', // выбранный код ИНИД
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
            }
        },
        computed: {
            // Тип данных выбранного поля ИНИД
            dataType: function () {
                if (this.ipcCode) {
                    return this.ipcCodes.find(x => x.id === parseInt(this.ipcCode)).data_type;
                }
                return '';
            },

            ipcCodesFiltered: function () {
                // Фильтр по объекту пром. собств.
                let ipcCodes = this.ipcCodes.filter(item => item.obj_type_id === parseInt(this.objType));

                // Получение реестров (заявки, охр. документы)
                let selectedScheduleTypes = [];
                this.objState.forEach(item => {
                    let schedule_types = this.objStates.find(x => x.id === parseInt(item)).schedule_types;
                    selectedScheduleTypes.push(...schedule_types);
                });

                // Фильтр по реестрам
                ipcCodes = ipcCodes.filter(item => item.schedule_types.some(x => selectedScheduleTypes.includes(x)));
                return ipcCodes;
            },

            translations: function () {
                return {
                    objType: gettext('Об\'єкт промислової власності'),
                    objState: gettext('Правовий статус ОПВ'),
                    ipcCode: gettext('Бібліографічні елементи'),
                    value: gettext('Значення'),
                    validationErrors: {
                        required: gettext('Обов\'язкове поле для заповнення'),
                        validQuery: gettext('Поле містить невірне значення'),
                    },
                }
            }
        },
        watch: {
            ipcCodesFiltered: function (val) {
                this.$nextTick(function () {
                    $(this.$refs.ipc_code.$el).trigger('chosen:updated');
                });
            }
        }
    }
</script>

<style lang="scss">
    .dropdown-header {
        font-weight: 600;
        font-size: 1.1rem !important;
        span.text {
            color: #0a0a0a;
        }
    }

    .dropdown-menu.show {
        max-width: 700px !important;
    }

    .dropdown-item {
        span.text-muted {
            display: none !important;
        }
    }

    .u-has-error-v1 {
        .chosen-choices {
            background-color: #fff0f0;
        }
    }
</style>