<template>
    <form class="g-brd-around g-brd-gray-light-v4 g-px-30 g-py-20">
        <h4 class="h6 g-font-weight-700 g-mb-20">Для початку роботи заповніть форму пошуку:</h4>

        <div class="row">
            <!-- Параметр пошуку -->
            <div class="col-md-5">
                <div class="form-group g-mb-20">
                    <chosen-select
                            class="w-100 h-100 u-select-v1 g-rounded-4 g-color-main g-color-primary--hover g-pt-8 g-pb-9"
                            data-placeholder="Оберіть параметр пошуку">
                        <option></option>
                        <option class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                value="">Номер заявки
                        </option>
                        <option class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                value="">Дата заявки
                        </option>
                        <option class="g-brd-none g-color-black g-color-white--hover g-color-white--active g-bg-primary--hover g-bg-primary--active"
                                value="">Номер охоронного документа
                        </option>
                    </chosen-select>
                </div>
            </div>
            <!-- End Параметр пошуку -->

            <!-- Значення параметра пошуку -->
            <div class="col-md-7 d-flex">
                <div class="form-group g-mb-20 g-pos-rel" style="flex-grow: 1">
                    <input class="form-control form-control-md g-brd-gray-light-v7 g-brd-gray-light-v3--focus g-rounded-4 g-px-14 g-pt-10 g-pb-11"
                           type="text"
                           placeholder="Значення">
                </div>
                <!-- Кнопка скрытия -->
                <button class="btn btn-md u-btn-pink g-pt-10 g-pb-11 g-ml-10 align-self-start"
                        type="button"
                ><i class="fa fa-minus"></i></button>
                <!-- End Кнопка скрытия -->
            </div>
            <!-- End Значення параметра пошуку -->
        </div>

        <!-- Дії -->
        <div class="row">
            <div class="col-md-6 text-center text-md-left g-mb-20 g-mb-0--md">
                <button type="button"
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
    import ChosenSelect from "./ChosenSelect.vue";

    export default {
        name: "SimpleSearchForm",
        components: {ChosenSelect}
    }
</script>

<style scoped>

</style>