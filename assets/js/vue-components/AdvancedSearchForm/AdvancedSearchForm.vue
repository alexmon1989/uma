<template>
    <form class="g-brd-around g-brd-gray-light-v4 g-px-30 g-py-20">
        <div class="row">
            <div class="col-md-6">
                <!-- Об'єкт промислової власності -->
                <div class="form-group g-mb-20 g-mb-10--md">
                    <label class="g-mb-10" for="obj_type">Об'єкт промислової власності</label>
                    <chosen-select
                            class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-py-7"
                            multiple="multiple"
                            data-placeholder="Об'єкт промислової власності"
                            data-open-icon="fa fa-angle-down"
                            data-close-icon="fa fa-angle-up"
                            id="obj_type"
                            name="obj_type"
                            v-model="selectedObjTypes">
                        <option
                                class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                v-for="objType in objTypes"
                                :value="objType.id"
                                :key="objType.id"
                        >{{ objType.value }}
                        </option>
                    </chosen-select>
                    <div class="d-flex justify-content-between small">
                        <a href="#" @click.prevent="selectAllTypes()">Вибрати все</a><br>
                        <a href="#" @click.prevent="deselectAllTypes()">Скинути</a>
                    </div>
                </div>
                <!-- End Об'єкт промислової власності -->
            </div>

            <div class="col-md-6">
                <!-- Об'єкт промислової власності -->
                <div class="form-group g-mb-20 g-mb-10--md">
                    <label class="g-mb-10" for="obj_status">Стан об'єкта</label>
                    <chosen-select
                            class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-py-7"
                            multiple
                            data-placeholder="Стан об'єкта"
                            data-open-icon="fa fa-angle-down"
                            data-close-icon="fa fa-angle-up"
                            id="obj_status"
                            name="obj_status"
                            v-model="selectedObjStates">
                        <option
                                class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                v-for="objState in objStates"
                                v-bind:value="objState.id"
                                :key="objState.id"
                        >{{ objState.value }}
                        </option>
                    </chosen-select>

                    <div class="d-flex justify-content-between small">
                        <a href="#" @click.prevent="selectAllStates()">Вибрати все</a><br>
                        <a href="#" @click.prevent="deselectAllStates()">Скинути</a>
                    </div>
                </div>
                <!-- End Об'єкт промислової власності -->
            </div>
        </div>

        <hr class="g-brd-gray-light-v4 g-mx-minus-30 g-mt-5">

        <h3 class="d-flex align-self-center text-uppercase g-font-size-12 g-font-size-default--md g-color-black g-mb-20">
            Коди ІНІД</h3>

        <!-- Коди ІНІД -->
        <div class="form-group g-mb-10"
             v-for="(ipcGroup, index) in ipcGroups"
             :key="ipcGroup.id"
        >
            <ipc-code :ipc-codes-grouped="ipcCodesGrouped"
                      :selected-obj-types="selectedObjTypes"
                      :selected-obj-states="selectedObjStates"
                      :index="index"
                      v-on:remove-ipc-group="removeIpcGroup"
            ></ipc-code>
        </div>
        <!-- End Коди ІНІД -->

         <!-- Дії -->
        <div class="row">
            <div class="col-md-6 text-center text-md-left g-mb-20 g-mb-0--md">
                <button @click="addIpcGroup"
                        type="button"
                        class="btn btn-md u-btn-indigo"
                        :disabled="selectedObjTypes.length === 0 || selectedObjStates.length === 0"
                ><i class="fa fa-plus g-mr-5"></i>Додати параметр
                </button>
            </div>
            <div class="col-md-6 text-center text-md-right g-mb-20 g-mb-0--md">
                <button type="submit"
                        class="btn btn-md u-btn-blue"
                ><i class="fa fa-search g-mr-5"></i>Показати результати
                </button>
            </div>
        </div>
        <!-- End Дії -->
    </form>
</template>

<script>
    import IpcCode from './IpcCode.vue';

    export default {
        name: "AdvancedSearchForm",
        props: {
            objTypes: Array,
            ipcCodes: Array,
        },
        data: function () {
            return {
                objStates: [
                    {'id': 1, 'value': 'Заявка', 'schedule_types': [9, 10, 11, 12, 13, 14, 15]},
                    {'id': 2, 'value': 'Охоронний документ', 'schedule_types': [3, 4, 5, 6, 7, 8]},
                ],
                ipcGroups: [
                    {'id': 1},
                ],
                selectedObjTypes: [],
                selectedObjStates: [],
                selectedScheduleTypes: [],
            }
        },
        computed: {
            // Фильтрует ИНИД-коды на основании выбранных значений полей "Об'єкт промислової власності", "Стан об'єкта"
            ipcCodesGrouped: function () {
                const self = this;
                // Фильтрация ИНИД-кодов
                const ipcCodesFiltered = this.ipcCodes.filter(function (item) {
                    return item.schedule_types.some(x => self.selectedScheduleTypes.includes(x))
                        && self.selectedObjTypes.some(x => x === item.obj_type_id.toString());
                });

                // Группировка ИНИД-кодов по объектам пром. собственности
                return this.selectedObjTypes.map(function (item) {
                    return {
                        'title': self.objTypes.find(x => x.id === parseInt(item)).value,
                        'ipc_codes': ipcCodesFiltered.filter(x => x.obj_type_id === parseInt(item))
                    }
                });
            }
        },
        watch: {
            // Получение scheduleTypes для выбранных состояний объекта ОПС
            selectedObjStates: function (val) {
                const self = this;
                let scheduleTypes = [];
                this.objStates.filter(function (item) {
                    return self.selectedObjStates.includes(item.id.toString())
                }).forEach(function (item) {
                    scheduleTypes = scheduleTypes.concat(item.schedule_types);
                });
                this.selectedScheduleTypes = scheduleTypes;
            }
        },
        methods: {
            // Добавляет группу полей для выбора кода ИНИД и его значения
            addIpcGroup: function () {
                this.ipcGroups.push({'id': (this.ipcGroups.length + 1)});
            },

            // Удаляет группу полей ИНИД
            removeIpcGroup: function (index) {
                this.ipcGroups.splice(index, 1);
            },

            // Выбор всех состояний объекта
            selectAllStates: function() {
                this.selectedObjStates = this.objStates.map(x => x.id.toString());
            },

            // Снять выбор всех состояний объекта
            deselectAllStates: function() {
                this.selectedObjStates = [];
            },

            // Выбор всех типов объекта
            selectAllTypes: function() {
                this.selectedObjTypes = this.objTypes.map(x => x.id.toString());
            },

            // Снять выбор всех типов объекта
            deselectAllTypes: function() {
                this.selectedObjTypes = [];
            }
        },
        components: {
            IpcCode
        }
    }
</script>

<style lang="scss">

</style>