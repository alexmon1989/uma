// Шаблон
import './template.js';
import Vue from 'vue';

import SimpleSearchForm from "./vue-components/SimpleSearchForm.vue";
import AdvancedSearchForm from "./vue-components/AdvancedSearchForm/AdvancedSearchForm.vue";

window.$ = window.jQuery = require('jquery');

// TODO: сделать нормально
Vue.component("chosen-select", {
    props: {
        value: [String, Array],
        multiple: Boolean
    },
    template: `<select :multiple="multiple"><slot></slot></select>`,
    mounted() {
        $(this.$el)
            .val(this.value)
            //.chosen()
            .on("change", e => this.$emit('input', $(this.$el).val()))
    },
    watch: {
        value(val) {
            $(this.$el).val(val).trigger('chosen:updated');
        }
    }
});


const app = new Vue({
    el: '#app',
    components: {
        SimpleSearchForm,
        AdvancedSearchForm
    }
});