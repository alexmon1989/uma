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

                <!-- Initializing Preloader -->
                <div v-if="initializing" class="text-center g-py-40">
                    <img src="/static/img/preloaders/loading.svg" alt="Loading..."/>
                    <div class="g-mt-15 g-font-size-14 g-font-weight-600 g-color-gray-dark-v2">
                        {{ translations.cryptoLoading }}
                    </div>
                </div>
                <!-- End Initializing Preloader -->

                <!-- Software installation needed banner -->
                <div v-else-if="softwareNeedsInstall" class="alert alert-warning rounded-0 g-mb-20" role="alert">
                    <h4 class="h6 g-font-weight-600 mb-2">
                        <i class="fa fa-exclamation-triangle g-mr-5"></i>
                        {{ isNativeNeedUpdate ? translations.softwareNeedUpdate : translations.softwareNeedInstall }}
                    </h4>
                    <div class="g-mb-10" v-if="downloadSoftwareUrl">
                        <a :href="downloadSoftwareUrl" target="_blank" class="btn btn-sm u-btn-primary rounded">
                            <i class="fa fa-download g-mr-5"></i>
                            {{ translations.downloadSoftware }}
                        </a>
                    </div>
                    <div class="g-mb-15" v-if="isWebExtensionNeeded && webExtensionInstallUrl">
                        <p class="g-font-size-13 mb-2">{{ translations.webExtensionNeedInstall }}</p>
                        <a :href="webExtensionInstallUrl" target="_blank" class="btn btn-sm u-btn-outline-primary rounded">
                            <i class="fa fa-puzzle-piece g-mr-5"></i>
                            {{ translations.installExtension }}
                        </a>
                    </div>
                    <button class="btn btn-sm u-btn-indigo rounded" type="button" @click="checkAndInit">
                        <i class="fa fa-refresh g-mr-5"></i>
                        {{ translations.checkAgain }}
                    </button>
                </div>
                <!-- End Software installation banner -->

                <!-- Form -->
                <form class="g-py-15" @submit.prevent="submitLogin" v-else>
                    <div class="mb-4">
                        <label class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.selectCA }}</label>
                        <select class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                                id="CAsServersSelectHardware"
                                v-model="selectedCA">
                            <option value="">{{ translations.autoDetectCA }}</option>
                            <option v-for="(ca, idx) in CAs" :key="idx" :value="ca.issuerCNs[0]">
                                {{ ca.issuerCNs[0] }}
                            </option>
                            <option value="other">{{ translations.otherCA }}</option>
                        </select>
                    </div>

                    <!-- Token Device Select -->
                    <div class="form-group">
                        <label class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.hardwareMedia }}</label>

                        <div class="input-group">
                            <select class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                                    id="KeyMediaSelect"
                                    v-model="selectedKeyMediaName"
                                    :disabled="keyMedias.length === 0">
                                <option value="" disabled v-if="keyMedias.length === 0">{{ translations.noHardwareMediaFound }}</option>
                                <option v-for="(km, idx) in keyMedias" :key="idx" :value="km.visibleName">
                                    {{ km.visibleName }}
                                </option>
                            </select>
                            <div class="input-group-append">
                                <button class="btn btn-md u-btn-brown rounded g-py-15 g-px-15 g-color-white"
                                        type="button"
                                        :disabled="refreshingMedias"
                                        :title="translations.refreshMedia"
                                        @click.prevent="refreshKeyMedias(true)">
                                    <i class="fa fa-refresh" :class="{ 'fa-spin': refreshingMedias }"></i>
                                    <span class="g-ml-5 d-none d-sm-inline">{{ translations.refreshMedia }}</span>
                                </button>
                            </div>
                        </div>
                        <small class="form-text text-muted" v-if="keyMedias.length === 0">
                            {{ translations.noHardwareMediaFound }}
                        </small>
                    </div>
                    <!-- End Token Device Select -->

                    <div class="form-group g-mb-25">
                        <label for="HardwareKeyPassword"
                               class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.tokenPassword }}</label>
                        <input type="password"
                               class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                               id="HardwareKeyPassword"
                               v-model="password"
                               :disabled="!selectedKeyMediaName"
                               :placeholder="translations.tokenPassword">
                    </div>

                    <div class="row justify-content-between mt-4">
                        <div class="col-6 align-self-center">
                            <label class="form-check-inline u-check g-color-gray-dark-v3 g-font-size-13 g-pl-25 mb-0">
                                <input class="g-hidden-xs-up g-pos-abs g-top-0 g-left-0"
                                       type="checkbox"
                                       id="RememberMeHardware"
                                       v-model="rememberMe"
                                       value="1">
                                <div class="u-check-icon-checkbox-v6 g-absolute-centered--y g-left-0">
                                    <i class="fa" data-check-icon=""></i>
                                </div>
                                {{ translations.rememberMe }}
                            </label>
                        </div>
                        <div class="col-6 align-self-center text-right">
                            <button class="btn btn-md u-btn-primary rounded g-py-13 g-px-25"
                                    type="submit"
                                    :title="translations.login"
                                    :disabled="!selectedKeyMediaName || loading"
                                    id="HardwareKeyReadButton">{{ translations.login }}</button>
                        </div>
                    </div>
                </form>
                <!-- End Form -->
            </div>
        </div>
    </div>
</template>

<script>
    import { translations } from './mixins/translations';
    import { cryptoMixin } from './mixins/crypto';

    export default {
        name: 'LoginHardwareKey',
        mixins: [translations, cryptoMixin],
        props: {
            secret: {
                type: String,
                required: true
            },
            nextUrl: {
                type: String,
                default: ''
            },
            active: {
                type: Boolean,
                default: false
            }
        },
        data() {
            return {
                euSign: null,
                initializing: Boolean(this.active),
                loadingInit: false,
                hasInitialized: false,
                loading: false,
                refreshingMedias: false,
                isFetchingMedias: false,
                pollTimer: null,
                error: '',
                softwareNeedsInstall: false,
                nativeInstallUrl: '',
                nativeUpdateUrl: '',
                isNativeNeedUpdate: false,
                webExtensionInstallUrl: '',
                isWebExtensionNeeded: false,
                selectedCA: '',
                CAs: [],
                keyMedias: [],
                selectedKeyMediaName: '',
                password: '',
                rememberMe: false
            };
        },
        computed: {
            downloadSoftwareUrl() {
                return this.isNativeNeedUpdate
                    ? (this.nativeUpdateUrl || this.nativeInstallUrl)
                    : (this.nativeInstallUrl || this.nativeUpdateUrl);
            }
        },
        watch: {
            active(isActive) {
                if (isActive) {
                    if (!this.hasInitialized) {
                        this.startInit();
                    } else {
                        this.resetTokenSession();
                        this.refreshKeyMedias(false);
                        this.startMediaPolling();
                    }
                } else {
                    this.stopMediaPolling();
                    this.resetTokenSession();
                }
            }
        },
        mounted() {
            if (this.active) {
                this.startInit();
            }
        },
        beforeDestroy() {
            this.stopMediaPolling();
            this.resetTokenSession();
        },
        methods: {
            startInit() {
                if (this.hasInitialized || this.loadingInit) return;
                this.loadingInit = true;
                this.initializing = true;
                this.ensureCryptoLoaded()
                    .then(() => {
                        this.checkAndInit();
                    })
                    .catch(err => {
                        console.error("Crypto script load error:", err);
                        this.error = this.translations.cryptoNotLoaded;
                        this.initializing = false;
                        this.loadingInit = false;
                    });
            },

            checkAndInit() {
                this.initializing = true;
                this.error = '';
                this.softwareNeedsInstall = false;

                try {
                    this.euSign = new window.EndUser(
                        null,
                        window.EndUserConstants.EndUserLibraryType.SW
                    );
                } catch (e) {
                    console.error("Failed to create EndUser SW instance:", e);
                    this.softwareNeedsInstall = true;
                    this.initializing = false;
                    this.loadingInit = false;
                    return;
                }

                this.euSign.GetLibraryInfo()
                    .then(info => {
                        if (!info.supported) {
                            this.error = this.translations.softwareNotSupported;
                            this.initializing = false;
                            this.loadingInit = false;
                            return;
                        }
                        if (!info.loaded) {
                            this.softwareNeedsInstall = true;
                            this.isNativeNeedUpdate = Boolean(info.isNativeLibraryNeedUpdate);
                            this.nativeInstallUrl = info.nativeLibraryInstallURL || '';
                            this.nativeUpdateUrl = info.nativeLibraryUpdateURL || '';
                            this.isWebExtensionNeeded = Boolean(info.isWebExtensionSupported && !info.isWebExtensionInstalled);
                            this.webExtensionInstallUrl = info.webExtensionInstallURL || '';
                            this.initializing = false;
                            this.loadingInit = false;
                            return;
                        }

                        this.initHardwareCrypto();
                    })
                    .catch(err => {
                        console.error("GetLibraryInfo error:", err);
                        this.softwareNeedsInstall = true;
                        this.initializing = false;
                        this.loadingInit = false;
                    });
            },

            initHardwareCrypto() {
                this.euSign.IsInitialized()
                    .then(isInit => {
                        if (isInit) return;
                        return this.euSign.Initialize(this.getEuSettings());
                    })
                    .then(() => {
                        return this.resetTokenSession();
                    })
                    .then(() => {
                        return this.euSign.GetCAs();
                    })
                    .then(cas => {
                        this.CAs = cas || [];
                        return this.refreshKeyMedias();
                    })
                    .then(() => {
                        this.hasInitialized = true;
                        this.initializing = false;
                        this.loadingInit = false;
                        if (this.active) {
                            this.startMediaPolling();
                        }
                    })
                    .catch(err => {
                        console.error("Crypto init error:", err);
                        this.error = `${this.translations.cryptoInitError}: ${err.message || err.toString()}`;
                        this.initializing = false;
                        this.loadingInit = false;
                    });
            },

            startMediaPolling() {
                this.stopMediaPolling();
                this.pollTimer = setInterval(() => {
                    if (this.active && this.hasInitialized && !this.loading && !this.isFetchingMedias) {
                        this.refreshKeyMedias(false);
                    }
                }, 3000);
            },

            stopMediaPolling() {
                if (this.pollTimer) {
                    clearInterval(this.pollTimer);
                    this.pollTimer = null;
                }
            },

            async filterHardwareKeyMedias(medias) {
                if (!medias || !medias.length) return [];

                // Знаходимо ядро EUSignCP у ланцюжку m_library (в euscp.js воно на 3 рівні вкладеності)
                let euSignCore = this.euSign;
                while (euSignCore && typeof euSignCore.IsHardwareKeyMedia !== 'function') {
                    euSignCore = euSignCore.m_library;
                }

                if (!euSignCore || typeof euSignCore.IsHardwareKeyMedia !== 'function') {
                    console.warn("IsHardwareKeyMedia method not found in EUSign hierarchy");
                    return medias;
                }

                const checks = await Promise.all(
                    medias.map(km => new Promise(resolve => {
                        try {
                            euSignCore.IsHardwareKeyMedia(
                                km.typeIndex,
                                km.devIndex,
                                '',
                                (isHW) => resolve(Boolean(isHW)),
                                () => resolve(false)
                            );
                        } catch (e) {
                            console.warn("IsHardwareKeyMedia exception for", km.visibleName, e);
                            resolve(false);
                        }
                    }))
                );

                return medias.filter((_, idx) => checks[idx]);
            },

            refreshKeyMedias(isManual = false) {
                if (!this.euSign || this.isFetchingMedias) return Promise.resolve();
                this.isFetchingMedias = true;
                if (isManual) {
                    this.refreshingMedias = true;
                }

                const finish = () => {
                    this.isFetchingMedias = false;
                    if (isManual) {
                        this.refreshingMedias = false;
                    }
                };

                return this.euSign.GetKeyMedias()
                    .then(medias => this.filterHardwareKeyMedias(medias || []))
                    .then(medias => {
                        const areEqual = this.keyMedias.length === medias.length &&
                            this.keyMedias.every((km, idx) => km.visibleName === medias[idx].visibleName);
                        if (!areEqual) {
                            this.keyMedias = medias;
                            if (this.keyMedias.length > 0) {
                                if (!this.selectedKeyMediaName || !this.keyMedias.find(m => m.visibleName === this.selectedKeyMediaName)) {
                                    this.selectedKeyMediaName = this.keyMedias[0].visibleName;
                                }
                            } else {
                                this.selectedKeyMediaName = '';
                            }
                        }
                        finish();
                    })
                    .catch(err => {
                        console.error("GetKeyMedias error:", err);
                        this.keyMedias = [];
                        this.selectedKeyMediaName = '';
                        finish();
                    });
            },

            async resetTokenSession() {
                if (this.euSign) {
                    await this.euSign.ResetPrivateKey().catch(() => {});
                }
            },

            async submitLogin() {
                const selectedKM = this.keyMedias.find(km => km.visibleName === this.selectedKeyMediaName);
                if (!selectedKM) {
                    this.error = this.translations.noTokenSelected;
                    return;
                }
                if (!this.password) {
                    this.error = this.translations.noTokenPassword;
                    return;
                }

                this.loading = true;
                this.error = '';

                const keyMedia = new window.EndUserKeyMedia(selectedKM);
                keyMedia.password = this.password;

                const caCN = (this.selectedCA && this.selectedCA !== 'other') ? this.selectedCA : null;

                try {
                    // 1. Обов'язково скидаємо попередню сесію закритого ключа в агенті EUSignClient,
                    // щоб токен не залишався розблокованим і вимагав обов'язкової автентифікації паролем.
                    await this.resetTokenSession();

                    // 2. Зчитуємо закритий ключ з токена
                    const ownerInfo = await this.euSign.ReadPrivateKey(keyMedia, null, caCN);

                    // 3. Підписуємо секрет сесії
                    const signedData = await this.euSign.SignData(this.secret, true);

                    // 4. Одразу після підпису знову блокуємо токен і очищаємо закритий ключ
                    await this.resetTokenSession();

                    // 5. Відправляємо запит на авторизацію на бекенд
                    const response = await this.sendAuthRequest({
                        ownerInfo: ownerInfo,
                        signedData: signedData,
                        caCN: caCN,
                        rememberMe: this.rememberMe,
                        keyType: 'hardware'
                    });

                    if (response.data && response.data.is_logged === 1) {
                        window.location.href = this.nextUrl || '/';
                    } else {
                        this.error = this.translations.authFailed;
                        this.loading = false;
                    }
                } catch (err) {
                    console.error("Hardware auth error:", err);
                    await this.resetTokenSession();
                    this.error = (err && (err.message || err.toString())) || this.translations.authError;
                    this.loading = false;
                }
            }
        }
    };
</script>

<style scoped>
    #KeyMediaSelect {
        -webkit-appearance: menulist !important;
        -moz-appearance: menulist !important;
        appearance: menulist !important;
    }
</style>
