<template>
    <div class="row">
        <div class="col-12 col-md-6">
            <div class="form-group u-select--v3 g-pos-rel g-brd-gray-light-v7 g-rounded-4 mb-0">
                <select class="selectpicker u-select--v3-select u-sibling show-tick"
                        :name="'form-' + index + '-ipc_code'"
                        data-live-search="true"
                        data-icon-base=""
                        data-width="100%"
                        data-tick-icon="hs-admin-check g-color-lightblue-v9"
                        title="Код ІНІД"
                        v-model="ipcCode"
                        :disabled="selectedObjTypes.length === 0 || selectedObjStates.length === 0"
                >
                    <optgroup v-for="group in ipcCodesGrouped" :label="group.title">
                        <option v-for="ipcCode in group.ipc_codes"
                            :value="ipcCode.id"
                            :key="ipcCode.id"
                            :data-content="ipcCode.value + '<span class=text-muted> (' + ipcCode.obj_type + ')</span>'"
                        >{{ ipcCode.value }}</option>
                    </optgroup>
                </select>

                <div class="d-flex align-items-center g-absolute-centered--y g-right-0 g-color-gray-light-v6 g-color-lightblue-v9--sibling-opened g-mr-15">
                    <i class="hs-admin-angle-down"></i>
                </div>
            </div>
        </div>

        <div class="col-12 col-md-6 d-flex">
            <div class="g-pos-rel" style="flex-grow: 1">
                <span class="g-pos-abs g-top-0 g-right-0 d-block g-width-40 h-100 opacity-0 g-opacity-1--success">
                    <i class="hs-admin-check g-absolute-centered g-font-size-default g-color-secondary"></i>
                </span>
                <input class="form-control form-control-md g-brd-gray-light-v7 g-brd-gray-light-v3--focus g-rounded-4 g-px-14 g-pt-10 g-pb-11"
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
            <button class="btn btn-md u-btn-primary g-pt-10 g-pb-11 g-ml-10 align-self-start"
                    type="button"
                    @click="$emit('remove-ipc-group', index)"
            ><i class="hs-admin-minus"></i></button>
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
                    let ipcCode = item.ipc_codes.find(x => x.id === self.ipcCode);
                    if (ipcCode) {
                        data_type = ipcCode.data_type;
                    }
                });
                return data_type;
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
</style>