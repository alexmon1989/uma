<template>
    <div class="row">
        <div class="col-md-12 text-center text-md-right g-mb-20 g-mb-0--md">
            <button :disabled="isFormSubmitting"
                    class="btn btn-md u-btn-blue"
            ><span v-if="isFormSubmitting">
                    <i class="fa fa-spinner g-mr-5"></i>{{ translations.performingSearch }}
                </span>
                <span v-else>
                        <i class="fa fa-search g-mr-5"></i>{{ translations.searchBtnText }}
                    </span>
            </button>
        </div>
    </div>
</template>

<script>
    import {translations} from "./mixins/translations";

    export default {
        name: "Actions",
        mixins: [translations],
        props: {
            isFormSubmitting: Boolean
        }
    }
</script>

<style scoped>

</style>