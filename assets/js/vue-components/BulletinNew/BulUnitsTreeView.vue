<template>
    <v-treeview
            class="bulletin-treeview g-line-height-1_3 g-font-size-13"
            style="display: inline-block; min-width: 100%"
            :active.sync="active"
            @update:active="$emit('input', $event[0])"
            :items="tree"
            activatable
            color="warning"
            open-on-click
            transition
    >
        <template v-slot:prepend="{ item, open }">
            <v-icon class="g-mr-7" v-if="item.type !== 'transaction_type'">
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
</template>

<script>
    export default {
        name: "BulUnitsTreeView",
        props: ['tree'],
        data() {
            return {
                active: [],
            }
        },
    }
</script>

<style scoped>

</style>