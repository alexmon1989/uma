<template>
    <form @submit.prevent="handleSubmit"
          class="g-brd-around g-brd-gray-light-v4 g-px-30 g-py-20">

        <input type="hidden" name="form-TOTAL_FORMS" :value="totalForms"/>
        <input type="hidden" name="form-INITIAL_FORMS" :value="initialData['form-INITIAL_FORMS'] || 1"/>
        <input type="hidden" name="form-MAX_NUM_FORMS" :value="initialData['form-MAX_NUM_FORMS']"/>

        <h4 class="h6 g-font-weight-700 g-mb-20">{{ translations.startText }}:</h4>

        <div v-for="(param, index) in searchParameters"
             :key="param.id">
            <search-param :search-parameter-types="searchParameterTypes"
                          :index="index"
                          :search-parameters-count="parseInt(totalForms)"
                          :initial-data="initialData"
                          v-on:remove-search-parameter="removeSearchParameter"
            />
        </div>

        <!-- Дії -->
        <div class="row">
            <div class="col-md-6 text-center text-md-left g-mb-20 g-mb-0--md">
                <button type="button"
                        @click="addSearchParameter"
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
    import SearchParam from "./SearchParam.vue";
    import axios from 'axios';

    export default {
        name: "SimpleSearchForm",
        components: {SearchParam},
        props: {
            searchParameterTypes: Array,
            initialData: Object
        },
        data() {
            return {
                searchParameters: [],

                translations: {
                    startText: gettext('Для початку роботи заповніть форму пошуку'),
                    selectParameter: gettext('Оберіть параметр пошуку'),
                    value: gettext('Значення'),
                    addBtnText: gettext('Додати параметр'),
                    searchBtnText: gettext('Показати результати'),
                },

                ipcModel: {},
                valueModel: {},
                totalForms: 1
            }
        },
        mounted() {
            // Поисковые параметры
            for (let i = 0; i < parseInt(this.initialData['form-TOTAL_FORMS']); i++) {
                this.searchParameters.push({'id': i});
            }

            // Количество форм
            this.totalForms = this.initialData['form-TOTAL_FORMS']
        },
        methods: {
            // Добавляет группу полей для выбора кода ИНИД и его значения
            addSearchParameter: function () {
                this.searchParameters.push({'id': (this.searchParameters[this.searchParameters.length - 1]['id'] + 1)});
                this.totalForms++;
            },

            // Удаляет группу полей ИНИД
            removeSearchParameter: function (index) {
                this.searchParameters.splice(index, 1);
                delete this.ipcModel['form-' + index + '-param_type'];
                delete this.valueModel['form-' + index + '-value'];
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
        created() {
            this.$validator.extend('validQuery', {
                validate: (value, args) => {
                    return new Promise((resolve, reject) => {
                        setTimeout(() => {
                            axios
                                .get('/search/validate-query/?search_type=simple&value='
                                    + value + '&param_type=' + args[0])
                                .then(response => resolve(response.data.result));
                        }, 200);
                    });
                }
            });
        }
    }
</script>

<style scoped>

</style>