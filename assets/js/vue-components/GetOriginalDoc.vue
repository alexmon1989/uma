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
                               v-validate="{ required: true, regex: /^(cr)?\d{10}$/i }"
                               data-vv-validate-on="none"
                               @input="errors.remove('sec_code')"
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
                    <small class="form-control-feedback" v-if="errors.has('sec_code')">{{ translations.validationErrors[errors.firstRule('sec_code')] }}</small>
                </div>
            </div>
        </form>

        <p class="g-mb-20 text-danger" v-if="serverErrors.length > 0">{{ typeof serverErrors[0] === 'string' ? serverErrors[0] : translations.serverErrors }}</p>
        <p class="g-mb-20 text-danger" v-if="notFound">{{ translations.notFound }}</p>
    </div>
</template>

<script>
    import axios from '../axios-config';
    import qs from 'qs';
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
                        regex: gettext('Довжина ідентифікатора документу невірна'),
                    },
                    serverErrors: gettext('Помилка звернення до сервера. Спробуйте, будь-ласка, пізніше.'),
                    rateLimitError: gettext('Забагато запитів. Будь-ласка, зачекайте хвилину перед повторною спробою.'),
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
                this.serverErrors = [];
                this.filePath = '';
                this.notFound = false;
                this.taskId = '';
                this.$validator.validate().then(valid => {
                    if (valid) {
                        Toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування файлу.'), {timeOut: 10000});
                        this.processing = true;
                        this.getTaskId();
                    } else {
                        this.processing = false;
                    }
                });
            },

            getTaskId() {
                axios.post('/services/original-document/create-task/', qs.stringify({
                    sec_code: this.value ? this.value.trim() : '',
                }))
                    .then((response) => {
                        this.serverErrors = [];
                        this.taskId = response.data.task_id;
                    })
                    .catch(e => {
                        if (e.response && e.response.status === 429) {
                            this.serverErrors.push(this.translations.rateLimitError);
                            Toastr.error(this.translations.rateLimitError);
                        } else if (e.response && e.response.data && e.response.data.error) {
                            this.serverErrors.push(e.response.data.error);
                            Toastr.error(e.response.data.error);
                        } else {
                            this.serverErrors.push(this.translations.serverErrors);
                            Toastr.error(this.translations.serverErrors);
                        }
                        this.processing = false;
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
                    let self = this;

                    let onSuccess = (response) => {
                        if (response.data.state === 'PENDING') {
                            return self.getTaskResult(--tries);
                        } else {
                            if (response.data.result) {
                                self.filePath = response.data.result;
                            } else {
                                self.notFound = true;
                            }
                            self.processing = false;
                        }
                    };

                    let onError = e => {
                        self.serverErrors.push(e);
                        Toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
                        self.processing = false;
                    };

                    return axios.get('/search/get-task-info/', {
                        params: {
                            task_id: self.taskId,
                        }
                    }).then(onSuccess).catch(onError);
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
                if (this.taskId) {
                  let tries = this.tries;
                  this.getTaskResult(tries);
                }
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
