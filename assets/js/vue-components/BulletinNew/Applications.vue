<template>
    <div>
        <p class="text-center g-font-weight-600 g-mb-10">Список об'єктів:</p>

        <v-treeview
                class="bulletin-treeview g-line-height-1_3 g-font-size-13"
                style="display: inline-block; min-width: 100%"
                :active.sync="active"
                @update:active="$emit('input', $event[0])"
                :items="applications"
                activatable
                color="warning"
                open-on-click
                transition
                v-if="applications"
        >
            <template v-slot:prepend="{ item, open }">
                <v-icon class="g-mr-7">
                    {{ 'mdi-file-document-outline' }}
                </v-icon>
            </template>
            <template v-slot:label="{ item }">
                <span :title="item.name">{{ item.name }}</span>
            </template>
        </v-treeview>

        <div class="d-flex justify-content-center g-mt-30" key="loading" v-else>
            <p class="text-danger" v-if="error">Помилка при отриманні даних. Спробуйте пізніше.</p>

            <v-progress-circular color="primary" indeterminate size="80" v-else></v-progress-circular>
        </div>
    </div>
</template>

<script>
    import axios from 'axios';

    export default {
        name: "Applications",
        props: ['bulId', 'bulUnitId'],
        data() {
            return {
                active: [],
                applications: false,
                error: false,
            }
        },

        created() {
            this.getApplications();
        },

        methods: {
            getApplications() {
                this.applications = false;
                axios
                    .get('/bulletin_new/get-applications/' + this.bulId + '/' + this.bulUnitId + '/')
                    .then(response => {
                        this.applications = response['data'];
                    }).catch(error => {
                    this.error = error;
                });
            }
        },

        watch: {
            bulUnitId() {
                this.getApplications();
            }
        }
    }
</script>

<style scoped>

</style>