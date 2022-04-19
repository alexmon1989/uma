<template>
    <v-card
            class="pt-6 mx-auto"
            flat
    >
        <transition name="application-fade" mode="out-in" v-on:after-enter="afterEnter">
            <div v-if="appData" key="data">
                <h3 class="h2 g-mb-20 text-center">Дані об'єкта</h3>

                <div v-html="appData"></div>
            </div>
            <div class="d-flex justify-content-center g-mt-10" key="loading" v-else>
                <p class="text-danger" v-if="error">Помилка при отриманні даних. Спробуйте пізніше.</p>

                <v-progress-circular color="primary" indeterminate size="80" v-else></v-progress-circular>
            </div>
        </transition>
    </v-card>
</template>

<script>
    import axios from 'axios';

    export default {
        name: "Application",

        props: ['appId'],

        data: () => ({
            appData: false,
            error: false,
        }),

        watch: {
            appId: function () {
                this.getAppData()
            },
        },

        mounted() {
            this.getAppData();
        },

        methods: {
            // Получение HTML заявки
            getAppData() {
                this.appData = false;
                this.error = false;
                axios
                    .get('/bulletin_new/detail/' + this.appId + '/')
                    .then(response => {
                        this.appData = response['data'];

                    }).catch(error => {
                        this.error = error
                    });
            },

            afterEnter() {
                $('[data-toggle="popover"]').popover();
                $.HSCore.components.HSPopup.init('.js-fancybox');
            }
        }
    }
</script>

<style scoped>
    .application-fade-enter-active, .application-fade-leave-active {
      transition: opacity .3s;
    }
    .application-fade-enter, .application-fade-leave-to {
      opacity: 0;
    }
</style>