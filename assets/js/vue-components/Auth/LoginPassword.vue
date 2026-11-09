<template>
    <div class="row justify-content-center g-mt-40">
        <div class="col-sm-10 col-md-9 col-lg-8 g-pos-rel">
            <div class="overlay" v-show="loading">
                <div class="overlay-content">
                    <img src="/static/img/preloaders/loading.svg" alt="Loading..."/>
                </div>
            </div>

            <div class="g-brd-around g-brd-gray-light-v2 rounded g-py-20 g-px-30">
                <!-- Alert Danger -->
                <div v-if="error"
                     class="alert fade show g-bg-red-opacity-0_1 g-color-lightred rounded-0"
                     role="alert">
                    <button type="button"
                            class="close u-alert-close--light g-ml-10 g-mt-1"
                            @click="error = ''"
                            aria-label="Close">
                        <span aria-hidden="true">×</span>
                    </button>

                    <div class="media">
                        <div class="media-body">
                            <p class="m-0 g-font-size-14" v-html="error"></p>
                        </div>
                    </div>
                </div>
                <!-- End Alert Danger -->

                <!-- Form -->
                <form class="g-py-15" @submit.prevent="submitLogin">
                    <div class="mb-4">
                        <label class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.usernameLabel }}</label>
                        <input class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                               type="text"
                               v-model.trim="username"
                               :disabled="loading"
                               :placeholder="translations.usernamePlaceholder">
                    </div>

                    <div class="mb-0">
                        <div>
                            <div class="row justify-content-between">
                                <div class="col align-self-center">
                                    <label class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.passwordLabel }}</label>
                                </div>
                            </div>
                            <input class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                                   type="password"
                                   v-model="password"
                                   :disabled="loading"
                                   :placeholder="translations.passwordPlaceholder">
                        </div>

                        <div class="row justify-content-between mt-4">
                            <div class="col-8 align-self-center">
                                <label class="form-check-inline u-check g-color-gray-dark-v3 g-font-size-13 g-pl-25 mb-0">
                                    <input class="g-hidden-xs-up g-pos-abs g-top-0 g-left-0"
                                           type="checkbox"
                                           v-model="rememberMe"
                                           :disabled="loading"
                                           value="1">
                                    <div class="u-check-icon-checkbox-v6 g-absolute-centered--y g-left-0">
                                        <i class="fa" data-check-icon=""></i>
                                    </div>
                                    {{ translations.rememberMe }}
                                </label>
                            </div>
                            <div class="col-4 align-self-center text-right">
                                <button class="btn btn-md u-btn-primary rounded g-py-13 g-px-25"
                                        :disabled="loading"
                                        type="submit">
                                    {{ translations.login }}
                                </button>
                            </div>
                        </div>
                    </div>
                </form>
                <!-- End Form -->
            </div>
        </div>
    </div>
</template>

<script>
    import axios from '../../axios-config';
    import { translations } from './mixins/translations';

    export default {
        name: 'LoginPassword',
        mixins: [translations],
        props: {
            nextUrl: {
                type: String,
                default: ''
            }
        },
        data() {
            return {
                username: '',
                password: '',
                rememberMe: false,
                loading: false,
                error: ''
            };
        },
        methods: {
            submitLogin() {
                if (!this.username || !this.password) {
                    this.error = this.translations.emptyCredentials;
                    return;
                }

                this.loading = true;
                this.error = '';

                const postData = new FormData();
                postData.append('username', this.username);
                postData.append('password', this.password);
                if (this.rememberMe) {
                    postData.append('remember_me', '1');
                }
                if (this.nextUrl) {
                    postData.append('next', this.nextUrl);
                }

                const langMatch = window.location.pathname.match(/^\/([a-z]{2})\//);
                const langPrefix = langMatch ? '/' + langMatch[1] : '/uk';
                const loginUrl = `${langPrefix}/auth/login_password/`;

                axios.post(loginUrl, postData)
                    .then(response => {
                        if (response.data && response.data.is_logged === 1) {
                            window.location.href = response.data.next || this.nextUrl || '/';
                        } else {
                            this.error = (response.data && response.data.error) || this.translations.invalidCredentials;
                            this.loading = false;
                        }
                    })
                    .catch(err => {
                        console.error('Password auth error:', err);
                        this.error = (err.response && err.response.data && err.response.data.error) ||
                            (err.message || this.translations.authError);
                        this.loading = false;
                    });
            }
        }
    };
</script>
