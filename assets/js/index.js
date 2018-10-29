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
        const $this = $(this.$el),
            searchMaxSelections = $this.data('max-selections'),
            setControlClasses = $this.data('control-classes'),
            setOpenIcon = $this.data('open-icon'),
            setCloseIcon = $this.data('close-icon'),
            setRtl = Boolean($this.data('rtl'));

        $this.val(this.value).chosen({
            inherit_select_classes: true,
            max_selected_options: searchMaxSelections ? searchMaxSelections : Infinity,
            rtl: setRtl ? setRtl : false
        }).on("change", e => this.$emit('input', $(this.$el).val()));

        if (setControlClasses) {
            $this.next().find('.chosen-single div').addClass(setControlClasses);
        }

        if (setOpenIcon) {
            $this.next().find('.chosen-single div b').append('<i class="' + setOpenIcon + '"></i>');

            if (setCloseIcon) {
                $this.next().find('.chosen-single div b').append('<i class="' + setCloseIcon + '"></i>');
            }
        }
    },
    watch: {
        value(val) {
            $(this.$el).val(val).trigger('chosen:updated');
        }
    },
    destroyed() {
        $(this.$el).chosen('destroy');
    }
});


const app = new Vue({
    el: '#app',
    components: {
        SimpleSearchForm,
        AdvancedSearchForm
    }
});