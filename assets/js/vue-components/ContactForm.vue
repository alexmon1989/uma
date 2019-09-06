<template>
    <div>
        <div v-if="serverErrors && serverErrors.length" class="alert alert-danger fade show g-my-20" role="alert">
            <h4 class="h5">
                <i class="fa fa-minus-circle"></i>
                {{ translations.errorsFounded }}
            </h4>
            <ul class="u-alert-list g-mt-10">
                <li v-for="(error, index) in serverErrors" :key="index">{{error.message}}</li>
            </ul>
        </div>

        <form @submit.prevent="sendMessage" v-if="!sended">
            <div class="row">
                <div :class="{'u-has-error-v1': errors.has('username') }" class="col-md-6 form-group g-mb-20">
                    <label class="g-color-gray-dark-v2 g-font-size-13">{{ translations.username }}:</label>
                    <input v-validate="'required'" data-vv-as="Имя" v-model="username" name="username"
                           :disabled="processing"
                           class="form-control g-color-gray-dark-v2 g-brd-gray-light-v4 g-brd-primary--focus rounded-3 g-py-13 g-px-15"
                           type="text">
                    <small v-show="errors.has('username')" class="form-control-feedback">{{ translations.validationErrors[errors.firstRule('username')] }}
                    </small>
                </div>

                <div :class="{'u-has-error-v1': errors.has('email') }" class="col-md-6 form-group g-mb-20">
                    <label class="g-color-gray-dark-v2 g-font-size-13">Email:</label>
                    <input v-validate="'required|email'" data-vv-as="Email" v-model="email" name="email"
                           :disabled="processing"
                           class="form-control g-color-gray-dark-v2 g-brd-gray-light-v4 g-brd-primary--focus rounded-3 g-py-13 g-px-15"
                           type="email">
                    <small v-show="errors.has('email')" class="form-control-feedback">{{ translations.validationErrors[errors.firstRule('email')] }}
                    </small>
                </div>

                <div class="col-md-12 form-group g-mb-20">
                    <label class="g-color-gray-dark-v2 g-font-size-13">{{ translations.subject }}:</label>
                    <input name="subject" v-model="subject" :disabled="processing"
                           class="form-control g-color-gray-dark-v2 g-brd-gray-light-v4 g-brd-primary--focus rounded-3 g-py-13 g-px-15"
                           type="text">
                </div>

                <div :class="{'u-has-error-v1': errors.has('message') }" class="col-md-12 form-group g-mb-40">
                    <label class="g-color-gray-dark-v2 g-font-size-13">{{ translations.message }}:</label>
                    <textarea v-validate="'required|min:20'" :disabled="processing" data-vv-as="Сообщение"
                              v-model="message"
                              name="message"
                              class="form-control g-color-gray-dark-v2 g-brd-gray-light-v4 g-brd-primary--focus g-resize-none rounded-3 g-py-13 g-px-15"
                              rows="7"></textarea>
                    <small v-show="errors.has('message')" class="form-control-feedback">{{ translations.validationErrors[errors.firstRule('message')] }}
                    </small>
                </div>
            </div>

            <button class="btn u-btn-primary rounded-3 g-py-12 g-px-20" type="submit" :disabled="processing"
                    role="button">
                {{ translations.sendMessage }}
            </button>

        </form>
        <p class="g-font-size-16 text-success" v-else>{{ translations.formSended }}</p>
    </div>
</template>

<script>
    import axios from '../axios-config';
    import qs from 'qs';

    export default {
        props: ['langCode'],
        data() {
            return {
                username: '',
                email: '',
                subject: '',
                phone: '',
                message: '',
                sended: false,
                processing: false,
                serverErrors: [],
                translations: {
                    formSended: gettext('Форму було відправлено. Ми відповимо вам найближчим часом.'),
                    errorsFounded: gettext('Знайдено помилки!'),
                    username: gettext('Ім\'я'),
                    subject: gettext('Тема'),
                    message: gettext('Повідомлення'),
                    sendMessage: gettext('Відправити повідомлення'),
                    validationErrors: {
                        required: gettext('Обов\'язкове поле для заповнення'),
                        email: gettext('Введіть вірну E-Mail адресу'),
                        min: gettext('Мінімальна довжина повідомлення має складати не менше 20 символів'),
                    },
                },
            }
        },
        methods: {
            sendMessage() {
                this.serverErrors = [];
                this.$validator.validateAll().then(result => {
                    if (result) {
                        this.processing = true;
                        axios.post('/' + this.langCode + '/contacts/', qs.stringify({
                            username: this.username,
                            email: this.email,
                            subject: this.subject,
                            message: this.message,
                        }))
                            .then(() => {
                                this.serverErrors = [];
                                this.sended = true;
                                this.processing = false;
                            })
                            .catch(e => {
                                this.serverErrors.push(e);
                                this.processing = false;
                            });
                    }
                });
            }
        }
    }
</script>

<style scoped>
</style>