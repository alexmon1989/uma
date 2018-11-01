<template>
    <form class="g-brd-around g-brd-gray-light-v4 g-px-30 g-py-20">

        <!-- Коди ІНІД -->
        <div class="form-group g-mb-10"
             v-for="(ipcGroup, index) in ipcGroups"
             :key="ipcGroup.id"
        >
            <ipc-code :obj-states="objStates"
                      :obj-types="objTypes"
                      :ipc-codes="ipcCodes"
                      :index="index"
                      :ipc-groups-count="ipcGroups.length"
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
                ]
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
            }
        },
        components: {
            IpcCode
        }
    }
</script>

<style lang="scss">

</style>