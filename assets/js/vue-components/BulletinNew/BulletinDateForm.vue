<template>
    <div class="row">
        <div class="col-12">
            <p class="g-font-weight-600">Для початку роботи оберіть рік та бюлетень та натисніть кнопку "Показати":</p>
        </div>

        <div class="col-md-5">
            <v-select
                    v-model="year"
                    :items="years"
                    label="Рік"
                    ref="yearSelect"
                    @blur="closeYearSelect"
                    @change="bulletinDate = ''"
            ></v-select>
        </div>

        <div class="col-md-5">
            <v-select
                    v-model="bulletinDate"
                    :items="buls_by_year"
                    item-text="title"
                    item-value="value"
                    label="Дата та номер бюлетеня"
                    ref="bulSelect"
                    @blur="closeBulSelect"
            ></v-select>
        </div>

        <div class="col-md-2 d-flex align-items-center">
            <v-btn
                    :disabled="bulletinDate === ''"
                    depressed
                    color="primary"
                    @click="setBulletinDate"
            >Показати</v-btn>
        </div>
    </div>

</template>

<script>
    export default {
        name: "BulletinDateForm",
        props: ['bulletins', 'initialBulletinDate'],

        data() {
            return {
                bulletinDate: '',
                year: '',

                years: [],
            }
        },

        created() {
            // Массив годов бюлетней
            this.years = this.bulletins.map(function(x) {
                return x[0];
            });
            this.years = [...new Set(this.years)].sort();

            if (this.initialBulletinDate) {
                this.year = parseInt(this.initialBulletinDate.substr(6, 10));
                this.bulletinDate = this.initialBulletinDate;
            }

            this.$emit('input', this.bulletinDate)
        },

        computed: {
            // Массив бюлетней выбранного года
            buls_by_year() {
                if (this.year) {
                    let buls = this.bulletins.filter(x => x[0] === this.year);

                    buls = buls.sort((a, b) => {
                        return a[2] > b[2];
                    });

                    return buls.map(x => {
                        return {'title': x[1] + ' - №' + x[2], 'value': x[1]};
                    });
                }

                return [];
            }
        },

        methods: {
            setBulletinDate() {
                window.location = '?bulletin_date=' + this.bulletinDate;
            },

            closeYearSelect() {
                this.$refs.yearSelect.blur();
            },

            closeBulSelect() {
                this.$refs.bulSelect.blur();
            }
        }
    }
</script>

<style lang="scss">
</style>