<template>
    <div class="g-bg-white g-brd-around g-brd-gray-light-v4 g-pa-25">
        <p class="g-mb-20">{{ translations.description }}</p>

        <form action="#" @submit.prevent="handleSubmit">
            <div class="row g-mb-5">
                <div class="col-lg-6 form-group"
                     :class="{ 'u-has-error-v1': errors.has('sec_code') }">
                    <div class="input-group">
                        <input type="text"
                               name="sec_code"
                               v-model="value"
                               v-validate="'required|alpha_num'"
                               :disabled="processing"
                               class="form-control rounded-0 form-control-md"
                               :placeholder="translations.inputPlaceholder">
                        <div class="input-group-append">
                            <button class="btn btn-md u-btn-primary rounded-0 g-width-180"
                                    type="submit"
                                    disabled
                                    v-if="processing"><i class="fa fa-spinner g-mr-5"></i>{{ translations.btnTextProcessing }}</button>
                            <button class="btn btn-md u-btn-primary rounded-0 g-width-180"
                                    type="submit"
                                    v-else><i class="fa fa-download g-mr-5"></i>{{ translations.btnText }}</button>
                        </div>
                    </div>
                    <small class="form-control-feedback" v-if="errors.has('sec_code')">{{ errors.first('sec_code') }}</small>
                </div>
            </div>
        </form>

        <p class="g-mb-20 text-danger" v-if="serverErrors.length > 0">{{ translations.serverErrors }}</p>
        <p class="g-mb-20 text-danger" v-if="notFound">{{ translations.notFound }}</p>
    </div>
</template>

<script>
    import axios from '../axios-config';
    import { saveAs } from 'file-saver';
    import * as Toastr from 'toastr';

    export default {
        data() {
            return {
                translations: {
                    description: gettext('Для отримання документу, будь-ласка, введіть його ідентифікатор та натисніть кнопку "Завантажити"'),
                    inputPlaceholder: gettext('Введіть ідентифікатор документу'),
                    btnText: gettext('Завантажити'),
                    btnTextProcessing: gettext('Зачекайте...'),
                    validationErrors: {
                        required: gettext('Обов\'язкове поле для заповнення'),
                        alpha_num: gettext('Поле містить невірне значення'),
                    },
                    serverErrors: gettext('Помилка звернення до сервера. Спробуйте, будь-ласка, пізніше.'),
                    notFound: gettext('Вибачте, за даним ідентифікатором не знайдено жодного документа.'),
                },
                processing: false,
                value: '',
                serverErrors: [],
                taskId: '',
                filePath: '',
                notFound: false,
                tries: 10,
            }
        },

        methods: {
            // Обработчик отправки формы
            handleSubmit() {
                Toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування файлу.'), {timeOut: 10000});
                this.serverErrors = [];
                this.processing = true;
                this.filePath = '';
                this.notFound = false;
                this.taskId = '';
                this.$validator.validate().then(valid => {
                    if (valid) {
                       this.getTaskId();
                    } else {
                        this.processing = false;
                    }
                });
            },

            getTaskId() {
                axios.get('/services/original-document/', {
                    params: {
                        sec_code: this.value,
                    }
                })
                    .then((response) => {
                        this.serverErrors = [];
                        this.taskId = response.data.task_id;
                    })
                    .catch(e => {
                        this.serverErrors.push(e);
                        this.processing = false
                    });
            },

            sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            },

            async getTaskResult(tries) {
                if (tries < this.tries) {
                    await this.sleep(1000);
                }

                if (tries > 0) {
                    return axios.get('/search/get-task-info/', {
                        params: {
                            task_id: this.taskId,
                        }
                    }).then((response) => {
                        if (response.data.state === 'PENDING') {
                            return this.getTaskResult(--tries);
                        } else {
                            if (response.data.result) {
                                this.filePath = response.data.result;
                            } else {
                                this.notFound = true;
                            }
                            this.processing = false
                        }
                    })
                    .catch(e => {
                        this.serverErrors.push(e);
                        Toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
                        this.processing = false;
                    });
                } else {
                    // Количество попыток превышено
                    this.serverErrors.push('Количество обращения к серверу превышено.');
                    Toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
                    this.processing = false;
                }
            },
        },

        watch: {
            taskId() {
                let tries = this.tries;
                this.getTaskResult(tries);
            },

            filePath(val) {
                if (val) {
                    Toastr.success(gettext('Файл було сформовано.'));
                    saveAs(val, val.split('/').pop());
                }
            }
        }
    }
</script>

<style scoped>

</style>