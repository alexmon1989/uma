<template>
    <div>
        <!-- Nav tabs -->
        <ul v-if="showTabs"
            class="nav justify-content-center u-nav-v2-1 u-nav-primary g-mb-20 g-font-size-18"
            role="tablist"
            data-target="nav-2-1-primary-hor-seperate"
            data-tabs-mobile-type="slide-up-down"
            data-btn-classes="btn btn-md btn-block rounded-0 u-btn-outline-primary g-mb-20">
            <li v-if="availableMethods.includes('file')" class="nav-item">
                <a class="nav-link g-brd-gray-light-v4 g-mx-5"
                   :class="{ active: currentTab === 'file' }"
                   href="#nav-2-1-primary-hor-seperate--1"
                   role="tab"
                   @click.prevent="currentTab = 'file'">{{ translations.tabFileKey }}</a>
            </li>
            <li v-if="availableMethods.includes('token')" class="nav-item">
                <a class="nav-link g-brd-gray-light-v4 g-mx-5"
                   :class="{ active: currentTab === 'token' }"
                   href="#nav-2-1-primary-hor-seperate--2"
                   role="tab"
                   @click.prevent="currentTab = 'token'">{{ translations.tabTokenKey }}</a>
            </li>
            <li v-if="availableMethods.includes('password')" class="nav-item">
                <a class="nav-link g-brd-gray-light-v4 g-mx-5"
                   :class="{ active: currentTab === 'password' }"
                   href="#nav-2-1-primary-hor-seperate--3"
                   role="tab"
                   @click.prevent="currentTab = 'password'">{{ translations.tabPassword }}</a>
            </li>
        </ul>
        <!-- End Nav tabs -->

        <!-- Tab panes -->
        <div id="nav-1-2-primary-hor-center" class="tab-content">
            <div v-if="availableMethods.includes('file')"
                 class="tab-pane fade"
                 :class="{ 'show active': currentTab === 'file' }"
                 id="nav-2-1-primary-hor-seperate--1"
                 role="tabpanel"
                 v-show="currentTab === 'file'">
                <login-file-key
                    :secret="secret"
                    :next-url="nextUrl"
                    :euscp-url="euscpUrl"
                    :worker-url="workerUrl"
                />
            </div>

            <div v-if="availableMethods.includes('token')"
                 class="tab-pane fade"
                 :class="{ 'show active': currentTab === 'token' }"
                 id="nav-2-1-primary-hor-seperate--2"
                 role="tabpanel"
                 v-show="currentTab === 'token'">
                <login-hardware-key
                    :secret="secret"
                    :next-url="nextUrl"
                    :active="currentTab === 'token'"
                    :euscp-url="euscpUrl"
                />
            </div>

            <div v-if="availableMethods.includes('password')"
                 class="tab-pane fade"
                 :class="{ 'show active': currentTab === 'password' }"
                 id="nav-2-1-primary-hor-seperate--3"
                 role="tabpanel"
                 v-show="currentTab === 'password'">
                <login-password :next-url="nextUrl" />
            </div>
        </div>
        <!-- End Tab panes -->
    </div>
</template>

<script>
    import LoginFileKey from './LoginFileKey.vue';
    import LoginHardwareKey from './LoginHardwareKey.vue';
    import LoginPassword from './LoginPassword.vue';
    import { translations } from './mixins/translations';

    export default {
        name: 'LoginForm',
        mixins: [translations],
        components: {
            LoginFileKey,
            LoginHardwareKey,
            LoginPassword
        },
        props: {
            authMethods: {
                type: Array,
                default: () => ['file', 'token', 'password']
            },
            secret: {
                type: String,
                default: ''
            },
            nextUrl: {
                type: String,
                default: ''
            },
            initialTab: {
                type: String,
                default: ''
            },
            euscpUrl: {
                type: String,
                default: ''
            },
            workerUrl: {
                type: String,
                default: ''
            }
        },
        computed: {
            availableMethods() {
                const valid = ['file', 'token', 'password'];
                return (this.authMethods && this.authMethods.length)
                    ? this.authMethods.filter(m => valid.includes(m))
                    : valid;
            },
            showTabs() {
                return this.availableMethods.length > 1;
            }
        },
        data() {
            const valid = ['file', 'token', 'password'];
            const methods = (this.authMethods && this.authMethods.length)
                ? this.authMethods.filter(m => valid.includes(m))
                : valid;
            const initial = (this.initialTab && methods.includes(this.initialTab))
                ? this.initialTab
                : (methods[0] || 'file');

            return {
                currentTab: initial
            };
        }
    };
</script>

<style scoped>
    >>> .form-control:disabled,
    >>> .form-control[disabled] {
        background-color: #e9ecef !important;
        cursor: not-allowed;
    }

    >>> .form-control[readonly] {
        background-color: #fff !important;
        cursor: pointer;
    }
</style>
