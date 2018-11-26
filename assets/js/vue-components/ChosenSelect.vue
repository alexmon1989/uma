<template>
    <select :multiple="multiple"
            data-open-icon="fa fa-angle-down"
            data-close-icon="fa fa-angle-up">
        <slot></slot>
    </select>
</template>

<script>
    export default {
        name: "ChosenSelect",
        props: {
            value: [String, Array],
            multiple: Boolean
        },
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
                let $el = $(this.$el);
                $el.val(val).trigger('chosen:updated');

                // Изменение отступов
                if (val.length > 0) {
                    $el.next().addClass('has-selected-items');
                } else {
                    $el.next().removeClass('has-selected-items');
                }
            }
        },
        destroyed() {
            $(this.$el).chosen('destroy');
        }
    }
</script>

<style lang="scss">
    .chosen-container-single {
        .chosen-search {
            input[type="text"] {
                padding: inherit;
            }
        }
    }

    .chosen-container-single .chosen-default {
        color: #999 !important;
    }

    .chosen-disabled {
        opacity: 1 !important;
        cursor: default;
        background-color: #e9ecef;
    }

    .chosen-results {

        > li {
            padding: 7px 10px !important;
        }

    }

    .has-selected-items {
        .chosen-choices {
            margin-top: -5px;
            margin-bottom: -4px;
        }
    }
</style>