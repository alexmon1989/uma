<template>
    <v-card
            class="pt-6 mx-auto"
            flat
    >
        <transition name="application-fade" mode="out-in">
            <div v-if="html" v-html="html" key="data"></div>
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
        name: "Transactions",

        props: ['bulId', 'transactionTypeId'],

        data: () => ({
            html: '',
            error: false,
        }),

        watch: {
            transactionTypeId: function () {
                this.getTransactionHtml()
            },
        },

        mounted() {
            this.getTransactionHtml();
        },

        methods: {
            // Получение HTML оповещений
            getTransactionHtml() {
                this.html = '';
                this.error = false;
                axios
                    .get('/bulletin_new/transactions/' + this.bulId + '/' + this.transactionTypeId + '/')
                    .then(response => {
                        this.html = response['data'];
                    }).catch(error => {
                        this.error = error
                    });
            },
        }
    }
</script>

<style scoped>

</style>