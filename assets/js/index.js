import 'es6-promise/auto';
import 'babel-polyfill';

// Шаблон
import './template.js';

import Vue from 'vue';

import SimpleSearchForm from "./vue-components/SimpleSearchForm/SimpleSearchForm.vue";
import AdvancedSearchForm from "./vue-components/AdvancedSearchForm/AdvancedSearchForm.vue";
import TransactionsSearchForm from "./vue-components/TransactionsSearchForm/TransactionsSearchForm.vue";
import LoadingDots from "./vue-components/LoadingDots.vue";
import ContactForm from "./vue-components/ContactForm.vue";
import GetOriginalDoc from "./vue-components/GetOriginalDoc.vue";

import VeeValidate from 'vee-validate';
import * as Toastr from "toastr";
Vue.use(VeeValidate);

window.$ = window.jQuery = require('jquery');
window.toastr = Toastr;

const app = new Vue({
    el: '#app',
    components: {
        SimpleSearchForm,
        AdvancedSearchForm,
        TransactionsSearchForm,
        LoadingDots,
        ContactForm,
        GetOriginalDoc,
    }
});