import 'es6-promise/auto';
import 'babel-polyfill';


import Vue from 'vue';
// Шаблон
import './template.js';

import vuetify from './plugins/vuetify'

import Multiselect from 'vue-multiselect';

import SimpleSearchForm from "./vue-components/SimpleSearchForm/SimpleSearchForm.vue";
import AdvancedSearchForm from "./vue-components/AdvancedSearchForm/AdvancedSearchForm.vue";
import TransactionsSearchForm from "./vue-components/TransactionsSearchForm/TransactionsSearchForm.vue";
import LoadingDots from "./vue-components/LoadingDots.vue";
import ContactForm from "./vue-components/ContactForm.vue";
import GetOriginalDoc from "./vue-components/GetOriginalDoc.vue";
import DateFilterForm from "./vue-components/DateFilterForm/DateFilterForm.vue";
import Bulletin from "./vue-components/Bulletin/Bulletin.vue";

import VeeValidate from 'vee-validate';
import * as Toastr from "toastr";
Vue.use(VeeValidate);

Vue.component('multiselect', Multiselect);

window.$ = window.jQuery = require('jquery');
window.toastr = Toastr;

const app = new Vue({
    vuetify,
    el: '#app',
    components: {
        SimpleSearchForm,
        AdvancedSearchForm,
        TransactionsSearchForm,
        LoadingDots,
        ContactForm,
        GetOriginalDoc,
        DateFilterForm,
        Bulletin,
    }
});