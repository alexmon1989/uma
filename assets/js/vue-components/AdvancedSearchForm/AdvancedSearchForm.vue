<template>
    <form @submit.prevent="handleSubmit"
          class="g-brd-around g-brd-gray-light-v4 g-px-30 g-py-20">
        <input type="hidden" name="form-TOTAL_FORMS" :value="totalForms"/>
        <input type="hidden" name="form-INITIAL_FORMS" :value="initialData['form-INITIAL_FORMS'] || 1"/>
        <input type="hidden" name="form-MAX_NUM_FORMS" :value="initialData['form-MAX_NUM_FORMS']"/>

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
                      :initial-data="initialData"
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
                ><i class="fa fa-plus g-mr-5"></i>{{ translations.addBtnText }}
                </button>
            </div>
            <div class="col-md-6 text-center text-md-right g-mb-20 g-mb-0--md">
                <button type="submit"
                        class="btn btn-md u-btn-blue"
                ><i class="fa fa-search g-mr-5"></i>{{ translations.searchBtnText }}
                </button>
            </div>
        </div>
        <!-- End Дії -->
    </form>
</template>

<script>
    import IpcCode from './IpcCode.vue';
    import axios from 'axios';

    export default {
        name: "AdvancedSearchForm",
        props: {
            objTypes: Array,
            ipcCodes: Array,
            initialData: Object
        },
        data: function () {
            return {
                objStates: [
                    {'id': 1, 'value': gettext('Заявка'), 'schedule_types': [9, 10, 11, 12, 13, 14, 15]},
                    {'id': 2, 'value': gettext('Охоронний документ'), 'schedule_types': [3, 4, 5, 6, 7, 8]},
                ],
                ipcGroups: [],
                totalForms: 1
            }
        },
        mounted() {
            // Группы ИНИД-кодов (поисковые)
            for (let i = 0; i < parseInt(this.initialData['form-TOTAL_FORMS']); i++) {
                this.ipcGroups.push({'id': i});
            }

            // Количество форм
            this.totalForms = this.initialData['form-TOTAL_FORMS']
        },
        methods: {
            // Добавляет группу полей для выбора кода ИНИД и его значения
            addIpcGroup: function () {
                this.ipcGroups.push({'id': (this.ipcGroups.length + 1)});
                this.totalForms++;
            },

            // Удаляет группу полей ИНИД
            removeIpcGroup: function (index) {
                this.ipcGroups.splice(index, 1);
                this.totalForms--;
            },

            // Обработчик отправки формы
            handleSubmit: function () {
                this.$validator.validate().then(valid => {
                    if (valid) {
                        document.forms[0].submit();
                    }
                });
            }
        },
        components: {
            IpcCode
        },
        computed: {
            translations: function () {
                return {
                    searchBtnText: gettext('Показати результати'),
                    addBtnText: gettext('Додати параметр')
                }
            }
        },
        created() {
            this.$validator.extend('validQuery', {
                validate: (value, args) => {
                    return new Promise((resolve, reject) => {
                        setTimeout(() => {
                            axios
                                .get('/search/validate-query/?search_type=advanced&value='
                                    + value + '&ipc_code=' + args[0]
                                    + '&obj_type=' + args[1]
                                    + '&obj_state=' + args[2].join('&obj_state='))
                                .then(response => resolve(response.data.result));
                        }, 200);
                    });
                }
            });
        }
    }
</script>

<style lang="scss">

</style>