<template>
    <div class="vuetify-wrap">
        <v-card>
            <v-card-title class="g-bg-primary g-color-white g-font-size-16 white--text headline">
                Офіційний електронний бюлетень
            </v-card-title>
            <v-row
                    class="g-pa-10"
                    justify="space-between"
            >
                <v-col cols="6" md="5" style="overflow: auto; max-height: 75vh;">
                    <v-treeview
                            style="display: inline-block; min-width: 100%"
                            :active.sync="active"
                            :items="tree"
                            :load-children="fetchItems"
                            activatable
                            color="warning"
                            open-on-click
                            transition
                    >
                        <template v-slot:prepend="{ item, open }">
                            <v-icon class="g-mr-7" v-if="item.type !== 'application'">
                                {{ open ? 'mdi-folder-open' : 'mdi-folder' }}
                            </v-icon>
                            <v-icon class="g-mr-7" v-else>
                                {{ 'mdi-file-document-outline' }}
                            </v-icon>
                        </template>
                        <template v-slot:label="{ item }">
                            <span :title="item.name">{{ item.name }}</span>
                        </template>
                    </v-treeview>
                </v-col>

                <v-divider vertical></v-divider>

                <v-col class="d-flex text-center"
                       style="overflow-y: auto; max-height: 75vh;">
                    <v-scroll-y-transition mode="out-in">
                        <div
                                class="title grey--text text--lighten-1 font-weight-light"
                                v-if="!selected"
                        >Будь-ласка, оберіть об'єкт для перегляду його даних.
                        </div>
                        <application :app_number="selected.name" v-else></application>
                    </v-scroll-y-transition>
                </v-col>
            </v-row>
        </v-card>
    </div>
</template>

<script>
    import Application from "./Application.vue";

    export default {
        data: () => ({
            active: [],

            tree: [
                {
                    name: 'Бюлетень',
                    type: 'bulletin',
                    children: [],
                },
            ],

            applications: [],
        }),

        components: {
            Application
        },

        computed: {
            selected() {
                if (!this.active.length) return undefined;
                const id = this.active[0];
                return this.searchTree(this.tree[0], id);
            },
        },

        methods: {
            async fetchItems(item) {
                let url = '';

                if (item.type === 'bulletin') {
                    url = '/uk/bulletin/obj-types/'
                } else if (item.type === 'obj_type') {
                    url = '/uk/bulletin/unit-types/?obj_type_id=' + item.obj_type_id
                } else if (item.type === 'unit_type') {
                    url = '/uk/bulletin/years/?unit_type_id=' + item.unit_type_id
                } else if (item.type === 'year') {
                    url = '/uk/bulletin/months/?unit_type_id=' + item.unit_type_id + '&year=' + item.name
                } else if (item.type === 'month') {
                    url = '/uk/bulletin/dates/?unit_type_id=' + item.unit_type_id + '&year=' + item.year + '&month=' + item.month
                } else if (item.type === 'publication_date') {
                    url = '/uk/bulletin/applications/?unit_type_id=' + item.unit_type_id + '&publication_date=' + item.publication_date
                }

                return fetch(url)
                    .then(res => res.json())
                    .then(json => item.children.push(...json))
                    .catch(err => console.warn(err))
            },

            searchTree(element, matchingId) {
                if (element.id === matchingId) {
                    return element;
                } else if (element.children != null) {
                    let i;
                    let result = null;
                    for (i = 0; result == null && i < element.children.length; i++) {
                        result = this.searchTree(element.children[i], matchingId);
                    }
                    return result;
                }
                return null;
            }
        },
    }
</script>

<style scoped>

</style>