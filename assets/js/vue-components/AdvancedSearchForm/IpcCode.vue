<template>
    <div class="row">
        <div class="col-12 col-md-6">
            <div class="form-group g-mb-10">
                <chosen-select
                        ref="ipc_code"
                        class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                        data-placeholder="Оберіть код ІНІД"
                        data-open-icon="fa fa-angle-down"
                        data-close-icon="fa fa-angle-up"
                        id="obj_status"
                        :name="'form-' + index + '-ipc_code'"
                        v-model="ipcCode"
                        :disabled="selectedObjTypes.length === 0 || selectedObjStates.length === 0"
                >
                    <option value=""></option>
                    <optgroup v-for="group in ipcCodesGrouped" :label="group.title">
                        <option v-for="ipcCode in group.ipc_codes"
                            class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                            :value="ipcCode.id"
                            :key="ipcCode.id"
                        >{{ ipcCode.value }} <small class=text-muted>({{ ipcCode.obj_type }})</small></option>
                    </optgroup>
                </chosen-select>
            </div>
        </div>

        <div class="col-12 col-md-6 d-flex">
            <div class="g-pos-rel form-group g-mb-10" style="flex-grow: 1">
                <input class="form-control form-control-md g-brd-gray-light-v3--focus g-rounded-4 g-px-14 g-py-9"
                       :name="'form-' + index + '-value'"
                       placeholder="Значення"
                       v-model="value"
                       :disabled="selectedObjTypes.length === 0 || selectedObjStates.length === 0 || !ipcCode"
                       ref="value"
                       @focus="valueFocused = true"
                       @blur="onValueBlur"
                       type="text">

                    <ul class="u-list-inline g-pt-5"
                        v-show="valueFocused"
                        @focus="valueFocused = true"
                    >
                        <li class="list-inline-item g-mr-5"
                            v-for="(operator, index) in logicalOperators"
                            v-show="operator.dataTypes.includes(dataType)"
                            :key="index"
                        >
                            <button type="button"
                                    ref="logical_operator"
                                    class="btn btn-xs btn-secondary"
                                    :disabled="selectedObjTypes.length === 0 || selectedObjStates.length === 0"
                                    @click="onLogicalOperatorBtnClick(operator.value)"
                            >{{ operator.value }}</button>
                        </li>
                    </ul>
            </div>
            <button class="btn btn-md u-btn-pink g-pt-10 g-pb-11 g-ml-10 align-self-start"
                    type="button"
                    @click="$emit('remove-ipc-group', index)"
            ><i class="fa fa-minus"></i></button>
        </div>
    </div>
</template>

<script>
    export default {
        name: "ipcCode",
        props: ["ipcCodesGrouped", "selectedObjTypes", "selectedObjStates", "index"],
        methods: {
            // Обработчик события нажатия на кнопку "Логический оператор".
            onLogicalOperatorBtnClick: function (value) {
                this.value = this.value + value;
                this.$nextTick(function () {
                    this.$refs.value.focus();
                });
            },

            // Обработчик события потери фокуса поля "Значение".
            onValueBlur: function (e) {
                this.valueFocused = this.$refs.logical_operator.includes(e.relatedTarget);
                // Для срабатывания нажатия других кнопок
                if (!this.valueFocused && e.relatedTarget) {
                    e.relatedTarget.click();
                }
            }
        },
        data: function () {
            return {
                ipcCode: '', // выбранный код ИНИД
                value: '', // введенное значение для поиска
                valueFocused: false,
                // Логические операторы. dataTypes определяет какие доступны для каких типов кодов ИНИД
                logicalOperators: [
                    {
                        'value': ' ТА ',
                        'dataTypes': ['date', 'integer', 'geography', 'varchar']
                    },
                    {
                        'value': ' АБО ',
                        'dataTypes': ['date', 'integer', 'geography', 'varchar']
                    },
                    {
                        'value': ' НЕ ',
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
                const self = this;
                let data_type = '';
                this.ipcCodesGrouped.forEach(function (item) {
                    let ipcCode = item.ipc_codes.find(x => x.id === parseInt(self.ipcCode));
                    if (ipcCode) {
                        data_type = ipcCode.data_type;
                    }
                });
                return data_type;
            }
        },
        watch: {
            ipcCodesGrouped: function (val) {
                this.$nextTick(function () {
                    $(this.$refs.ipc_code.$el).trigger('chosen:updated');
                });
            }
        },
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
</style>