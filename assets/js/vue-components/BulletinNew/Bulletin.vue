<template>

    <div class="v-application vuetify-wrap" data-app>
        <bulletin-date-form :bulletins="bulletins"
                            :initial-bulletin-date="initialBulletinDate"
                            v-model="bulletinDate"></bulletin-date-form>

        <div v-if="bulletinDate">
            <v-card>
                <v-card-title class="g-bg-primary g-color-white g-font-size-16 white--text headline">
                    Офіційний електронний бюлетень №{{ bulletin[2] }} від {{ bulletinDate }}
                </v-card-title>
                <v-row
                        class="g-pa-10"
                        justify="space-between"
                >
                    <v-col cols="3" md="4" style="overflow: auto; height: 75vh;">
                        <bul-units-tree-view :tree="tree"
                                             v-model="activeItem"></bul-units-tree-view>
                    </v-col>
                    <v-divider vertical></v-divider>

                    <v-col cols="3" md="2" style="overflow: auto; height: 75vh;" v-if="activeItem && activeItemType !== 'transaction_type'">
                        <applications :bul-id="bulletin[3]"
                                      :bul-unit-id="activeItemId"
                                      v-model="application"></applications>
                    </v-col>
                    <v-divider vertical v-if="activeItem && activeItemType !== 'transaction_type'"></v-divider>

                    <v-col style="overflow-y: auto; height: 75vh;">
                        <application :app-id="application"
                                     v-if="application"></application>

                        <transactions v-else-if="activeItemType === 'transaction_type'"
                                      :bul-id="bulletin[3]"
                                      :transaction-type-id="activeItemId"></transactions>

                        <div class="d-flex justify-content-center"
                             v-else>
                            <p class="title grey--text text--lighten-1 font-weight-light g-pt-10 g-font-size-16"
                            >Будь-ласка, оберіть об'єкт для перегляду його даних.</p>
                        </div>
                    </v-col>
                </v-row>
            </v-card>
        </div>
    </div>
</template>

<script>
    import BulletinDateForm from "./BulletinDateForm.vue";
    import Application from "./Application.vue";
    import Applications from "./Applications.vue";
    import BulUnitsTreeView from "./BulUnitsTreeView.vue";
    import Transactions from "./Transactions.vue";

    export default {
        name: "Bulletin",
        props: ['bulletins', 'initialBulletinDate', 'tree'],
        components: {
            Applications,
            Application,
            BulletinDateForm,
            BulUnitsTreeView,
            Transactions,
        },

        data() {
            return {
                bulletinDate: '',
                activeItem: '',
                application: false,
            }
        },

        computed: {
            activeItemId() {
                if (this.activeItem) {
                    return this.activeItem.split('-')[1]
                }
                return null;
            },

            activeItemType() {
                if (this.activeItem) {
                    const res = this.findItemNested(this.tree, this.activeItem, "children");
                    return res.type;
                }
                return ''
            },

            // Выбранный бюлетень
            bulletin() {
                if (this.bulletinDate) {
                    return this.bulletins.find(x => x[1] === this.bulletinDate)
                }
            }
        },

        watch: {
            activeItem() {
                this.application = false;
            }
        },

        methods: {
            findItemNested(arr, itemId, nestingKey) {
                const self = this;
                return arr.reduce((a, item) => {
                    if (a) return a;
                    if (item.id === itemId) return item;
                    if (item[nestingKey]) return self.findItemNested(item[nestingKey], itemId, nestingKey)
                }, null)
            }
        }
    }

</script>

<style>
.v-label {
    transform-origin: top left;
}
</style>