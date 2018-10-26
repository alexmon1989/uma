<template>
    <form class="g-brd-around g-brd-gray-light-v4 g-px-30 g-py-20">
        <h4 class="h6 g-font-weight-700 g-mb-20">Для початку роботи заповніть форму пошуку:</h4>

        <div class="row g-mx-0--md">
            <!-- Параметр пошуку -->
            <div class="col-md-3 g-px-0 g-mb-20">
                <select class="js-custom-select w-100 h-100 u-select-v1 g-min-width-150 g-brd-gray-light-v3 g-color-black g-color-primary--hover g-pt-9 g-pb-4"
                        required
                        data-placeholder="Оберіть параметр пошуку"
                        data-open-icon="fa fa-angle-down"
                        data-close-icon="fa fa-angle-up">
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
                </select>
            </div>
            <!-- End Параметр пошуку -->

            <!-- Значення параметра пошуку -->
            <div class="col-md-8 g-px-0 g-mb-20">
                <input class="form-control rounded-0 g-brd-gray-light-v3 g-brd-left-none--md g-px-20 g-py-8" type="text"
                       placeholder="Значення">
            </div>
            <!-- End Значення параметра пошуку -->

            <!-- Кнопка скрытия -->
            <div class="col-md-1 g-px-0 g-mb-20">
                <a href="#!" class="btn btn-md rounded-0 btn-block u-btn-pink"><i class="fa fa-minus"></i></a>
            </div>
            <!-- End Кнопка скрытия -->
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
    export default {
        name: "SimpleSearchForm"
    }
</script>

<style scoped>

</style>