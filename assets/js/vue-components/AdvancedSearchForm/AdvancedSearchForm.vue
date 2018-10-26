<template>
    <form class="g-brd-around g-brd-gray-light-v4 g-px-30 g-py-20">
        <div class="row">
            <div class="col-md-6">
                <!-- Об'єкт промислової власності -->
                <div class="form-group g-mb-20">
                    <label class="g-mb-10" for="obj_type">Об'єкт промислової власності</label>
                    <chosen-select class="js-custom-select w-100 h-100 u-select-v1 g-min-width-150 g-brd-gray-light-v3 g-color-black g-color-primary--hover g-pt-7 g-pb-7"
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
                        >{{ objType.value }}</option>
                    </chosen-select>
                </div>
                <!-- End Об'єкт промислової власності -->
            </div>

            <div class="col-md-6">
                <!-- Об'єкт промислової власності -->
                <div class="form-group g-mb-20">
                    <label class="g-mb-10" for="obj_status">Стан об'єкта</label>
                    <chosen-select class="js-custom-select w-100 h-100 u-select-v1 g-min-width-150 g-brd-gray-light-v3 g-color-black g-color-primary--hover g-pt-7 g-pb-7"
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
                        >{{ objState.value }}</option>
                    </chosen-select>
                </div>
                <!-- End Об'єкт промислової власності -->
            </div>
        </div>

        <hr class="g-brd-gray-light-v4 g-mx-minus-30 g-mt-5">

        <h3 class="d-flex align-self-center text-uppercase g-font-size-12 g-font-size-default--md g-color-black g-mb-20">
            Коди ІНІД</h3>

        <!-- Коди ІНІД -->
        <div class="form-group g-mb-15"
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

        <div class="g-mb-10">
            <button @click="addIpcGroup"
                    type="button"
                    class="btn btn-md u-btn-primary"
                    :disabled="selectedObjTypes.length === 0 || selectedObjStates.length === 0"
            ><i class="hs-admin-plus g-mr-5"></i>Додати
            </button>
        </div>

        <div class="text-center">
            <button type="submit"
                    class="btn btn-xl u-btn-blue g-mr-10"
            ><i class="hs-admin-search g-mr-5"></i>Пошук
            </button>
        </div>
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
                        && self.selectedObjTypes.some(x => x === item.obj_type_id);
                });

                // Группировка ИНИД-кодов по объектам пром. собственности
                return this.selectedObjTypes.map(function (item) {
                    return {
                        'title': self.objTypes.find(x => x.id === parseInt(item)).value,
                        'ipc_codes': ipcCodesFiltered.filter(x => x.obj_type_id === item)
                    }
                });
            }
        },
        watch: {
            ipcCodesGrouped: function (val) {
                this.$nextTick(function () {
                    //$('.selectpicker').selectpicker('refresh');
                });
            },

            // Получение scheduleTypes для выбранных состояний объекта ОПС
            selectedObjStates: function (val) {
                const self = this;
                let scheduleTypes = [];
                this.objStates.filter(function (item) {
                    return self.selectedObjStates.includes(item.id)
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
                this.$nextTick(function () {
                    $('.selectpicker').selectpicker();
                });
            },

            // Удаляет группу полей ИНИД
            removeIpcGroup: function (index) {
                this.ipcGroups.splice(index, 1);
            },
        },
        components: {
            IpcCode
        }
    }
</script>

<style lang="scss">

</style>