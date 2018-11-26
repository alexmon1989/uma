<template>
    <form @submit.prevent="handleSubmit"
          class="g-brd-around g-brd-gray-light-v4 g-px-30 g-py-20">
        <h4 class="h6 g-font-weight-700 g-mb-20">{{ translations.startText }}:</h4>

        <div class="row g-mb-5"
             v-for="(param, index) in searchParameters"
             :key="param.id"
        >
            <!-- Параметр пошуку -->
            <div class="col-md-5 g-pr-7--md">
                <div class="form-group g-mb-15"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-param_type') }">
                    <chosen-select
                            class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                            :name="'form-' + index + '-param_type'"
                            v-validate="'required'"
                            :data-placeholder="translations.selectParameter">
                        <option></option>
                        <option v-for="(type, key) in searchParameterTypes"
                                :key="key"
                                class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                :value="type.id">{{ type.field_label }}
                        </option>
                    </chosen-select>
                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-param_type')">{{ translations.required_error }}</small>
                </div>
            </div>
            <!-- End Параметр пошуку -->

            <!-- Значення параметра пошуку -->
            <div class="col-md-6 g-px-8--md">
                <div class="form-group g-mb-20"
                     :class="{ 'u-has-error-v1': errors.has('form-' + index + '-value') }">
                    <input class="form-control form-control-md g-brd-gray-light-v7 g-brd-gray-light-v3--focus g-rounded-4 g-px-14 g-pt-10 g-pb-11"
                           type="text"
                           autocomplete="off"
                           :name="'form-' + index + '-value'"
                           v-validate="'required'"
                           :placeholder="translations.value">
                    <small class="form-control-feedback" v-if="errors.has('form-' + index + '-value')">{{ translations.required_error }}</small>
                </div>
            </div>
            <!-- End Значення параметра пошуку -->

            <div class="col-md-1 g-mb-30 g-mb-15--md g-pl-8--md">
                <button type="button"
                        class="btn btn-block btn-md u-btn-pink g-pt-10 g-pb-11 rounded-0"
                        @click="removeSearchParameter(index)"
                        :disabled="searchParameters.length === 1"
                ><i class="fa fa-minus"></i></button>
            </div>
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
    import ChosenSelect from "./ChosenSelect.vue";

    export default {
        name: "SimpleSearchForm",
        components: {ChosenSelect},
        props: {
            searchParameterTypes: Array,
        },
        data() {
            return {
                searchParameters: [
                    {'id': 1},
                ],

                translations: {
                    startText: gettext('Для початку роботи заповніть форму пошуку'),
                    selectParameter: gettext('Оберіть параметр пошуку'),
                    value: gettext('Значення'),
                    addBtnText: gettext('Додати параметр'),
                    searchBtnText: gettext('Показати результати'),
                    required_error: gettext('Обов\'язкове поле для заповнення'),
                }
            }
        },
        methods: {
            // Добавляет группу полей для выбора кода ИНИД и его значения
            addSearchParameter: function () {
                this.searchParameters.push({'id': (this.searchParameters[this.searchParameters.length - 1]['id'] + 1)});
            },

            // Удаляет группу полей ИНИД
            removeSearchParameter: function (index) {
                this.searchParameters.splice(index, 1);
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
    }
</script>

<style scoped>

</style>