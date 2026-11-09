<template>
    <div class="row justify-content-center g-mt-40">
        <div class="col-sm-10 col-md-9 col-lg-8 g-pos-rel">
            <div class="overlay" id="overlay" v-show="loading">
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

                <!-- Form -->
                <form class="g-py-15" @submit.prevent="submitLogin" v-else>
                    <div class="mb-4">
                        <label class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.selectCA }}</label>
                        <select class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                                id="CAsServersSelect"
                                v-model="selectedCA"
                                @change="onCAChange">
                            <option value="">{{ translations.autoDetectCA }}</option>
                            <option v-for="(ca, idx) in CAs" :key="idx" :value="ca.issuerCNs[0]">
                                {{ ca.issuerCNs[0] }}
                            </option>
                            <option value="other">{{ translations.otherCA }}</option>
                        </select>
                    </div>

                    <!-- File Input -->
                    <div class="form-group">
                        <label class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.privateKey }}</label>

                        <div class="input-group">
                            <input type="text"
                                    id="PKeyFileName"
                                    readonly
                                    :value="keyFileName"
                                    @click="triggerFileInput"
                                    class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                                    :placeholder="translations.privateKey">
                            <div class="input-group-append">
                                <a class="btn btn-md u-btn-brown rounded g-py-15 g-px-15 g-color-white"
                                    id="PKeySelectFileButton"
                                    href="#"
                                    @click.prevent="triggerFileInput">{{ translations.browse }}</a>
                                <input id="PKeyFileInput" ref="keyFileInput" type="file" style="display: none" @change="onKeyFileSelected">
                            </div>
                        </div>
                        <small id="ChoosePKFileText" class="form-text text-muted">{{ hintText }}</small>
                    </div>
                    <!-- End File Input -->

                    <!-- File Input -->
                    <div class="form-group" id="PKCertsSelectZone" v-if="needsCertificates">
                        <label class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.certificates }}</label>

                        <div class="input-group">
                            <input type="text"
                                    id="SelectedPKCertsList"
                                    readonly
                                    :value="certFilesNames"
                                    @click="triggerCertInput"
                                    class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                                    :placeholder="translations.certificates">
                            <div class="input-group-append">
                                <a class="btn btn-md u-btn-brown rounded g-py-15 g-px-15 g-color-white"
                                    id="ChoosePKCertsButton"
                                    href="#"
                                    @click.prevent="triggerCertInput">{{ translations.browse }}</a>
                                <input id="ChoosePKCertsInput" ref="certFileInput" type="file" style="display: none" multiple @change="onCertFilesSelected">
                            </div>
                        </div>
                        <small class="form-text text-muted">{{ translations.chooseCertsHint }}</small>
                    </div>
                    <!-- End File Input -->

                    <div class="form-group g-mb-25">
                        <label for="PKeyPassword"
                               class="g-color-gray-dark-v2 g-font-weight-600 g-font-size-13">{{ translations.keyPassword }}</label>
                        <input type="password"
                               class="form-control g-color-black g-brd-gray-light-v2 g-brd-primary--hover rounded g-py-15 g-px-15"
                               id="PKeyPassword"
                               v-model="password"
                               :disabled="!keyFile"
                               :placeholder="translations.keyPassword">
                    </div>

                    <div class="row justify-content-between mt-4">
                        <div class="col-6 align-self-center">
                            <label class="form-check-inline u-check g-color-gray-dark-v3 g-font-size-13 g-pl-25 mb-0">
                                <input class="g-hidden-xs-up g-pos-abs g-top-0 g-left-0"
                                       type="checkbox"
                                       id="RememberMe"
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
                                    :disabled="!keyFile || loading"
                                    id="PKeyReadButton">{{ translations.login }}</button>
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
        name: 'LoginFileKey',
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
            workerUrl: {
                type: String,
                required: true
            }
        },
        data() {
            return {
                euSign: null,
                initializing: true,
                loading: false,
                error: '',
                selectedCA: '',
                CAs: [],
                keyFile: null,
                keyFileName: '',
                certFiles: [],
                certFilesNames: '',
                password: '',
                rememberMe: false,
                needsCertificates: false
            };
        },
        computed: {
            hintText() {
                return this.translations.choosePKFileText +
                    (this.needsCertificates ? this.translations.choosePKCertText : "");
            }
        },
        mounted() {
            this.ensureCryptoLoaded()
                .then(() => {
                    this.initCrypto();
                })
                .catch(err => {
                    console.error("Crypto lib not loaded:", err);
                    this.error = this.translations.cryptoNotLoaded;
                    this.initializing = false;
                });
        },
        methods: {
            initCrypto() {
                if (!window.EndUser || !window.EndUserConstants) {
                    this.error = this.translations.cryptoNotLoaded;
                    this.initializing = false;
                    return;
                }

                this.euSign = new window.EndUser(
                    this.workerUrl,
                    window.EndUserConstants.EndUserLibraryType.JS
                );

                this.euSign.IsInitialized()
                    .then(isInit => {
                        if (isInit) return;
                        return this.euSign.Initialize(this.getEuSettings());
                    })
                    .then(() => {
                        return this.euSign.GetCAs();
                    })
                    .then(cas => {
                        this.CAs = cas || [];
                        this.initializing = false;
                    })
                    .catch(err => {
                        console.error("Crypto init error:", err);
                        this.error = `${this.translations.cryptoInitError}: ${err.message || err.toString()}`;
                        this.initializing = false;
                    });
            },

            triggerFileInput() {
                this.$refs.keyFileInput.click();
            },

            onKeyFileSelected(e) {
                const files = e.target.files;
                if (files && files.length === 1) {
                    this.keyFile = files[0];
                    this.keyFileName = files[0].name;
                    this.error = '';
                } else {
                    this.keyFile = null;
                    this.keyFileName = '';
                }
            },

            triggerCertInput() {
                if (this.loading) return;
                this.$refs.certFileInput.click();
            },

            onCertFilesSelected(e) {
                const files = e.target.files;
                if (files && files.length > 0) {
                    this.certFiles = Array.from(files);
                    this.certFilesNames = this.certFiles.map(f => f.name).join(', ');
                } else {
                    this.certFiles = [];
                    this.certFilesNames = '';
                }
            },

            onCAChange() {
                if (this.selectedCA === 'other') {
                    this.needsCertificates = true;
                    return;
                }
                if (!this.selectedCA) {
                    this.needsCertificates = false;
                    return;
                }
                const caServer = this.CAs.find(ca => ca.issuerCNs && ca.issuerCNs.indexOf(this.selectedCA) !== -1);
                this.needsCertificates = Boolean(!caServer || (!caServer.cmpAddress && !caServer.certsInKey));
            },

            readFile(file) {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onloadend = (evt) => {
                        if (evt.target.readyState !== FileReader.DONE) return;
                        resolve({
                            file: file,
                            data: new Uint8Array(evt.target.result)
                        });
                    };
                    reader.onerror = (err) => reject(err);
                    reader.readAsArrayBuffer(file);
                });
            },

            readCertificates(files) {
                if (!files || files.length === 0) {
                    return Promise.resolve(null);
                }
                const promises = files.map(f => this.readFile(f));
                return Promise.all(promises).then(results => results.map(r => r.data));
            },

            readPrivateKey(file, password, pkCertificates, caCN) {
                return this.readFile(file).then(result => {
                    // Підтримка контейнерів JKS
                    if (result.file.name.toLowerCase().endsWith(".jks")) {
                        return this.euSign.GetJKSPrivateKeys(result.data).then(jksKeys => {
                            if (!jksKeys || jksKeys.length === 0) {
                                throw new Error(this.translations.jksNoKeys);
                            }
                            const pkIndex = 0;
                            const jksCerts = (jksKeys[pkIndex].certificates || []).map(c => c.data);
                            const certsToUse = (pkCertificates && pkCertificates.length > 0) ? pkCertificates : jksCerts;
                            return this.euSign.ReadPrivateKeyBinary(
                                jksKeys[pkIndex].privateKey,
                                password,
                                certsToUse,
                                caCN
                            );
                        });
                    }

                    // Стандартний бінарний файл ключа
                    return this.euSign.ReadPrivateKeyBinary(
                        result.data,
                        password,
                        pkCertificates,
                        caCN
                    );
                });
            },

            submitLogin() {
                if (!this.keyFile) {
                    this.error = this.translations.noKeySelected;
                    return;
                }
                if (this.needsCertificates && (!this.certFiles || this.certFiles.length === 0)) {
                    this.error = this.translations.noCertSelected;
                    return;
                }
                if (!this.password) {
                    this.error = this.translations.noPassword;
                    return;
                }
                
                this.loading = true;
                this.error = '';

                const caCN = (this.selectedCA && this.selectedCA !== 'other') ? this.selectedCA : null;

                this.readCertificates(this.certFiles)
                    .then(pkCertificates => {
                        return this.readPrivateKey(this.keyFile, this.password, pkCertificates, caCN);
                    })
                    .then(ownerInfo => {
                        return this.euSign.SignData(this.secret, true).then(signedData => ({
                            ownerInfo,
                            signedData
                        }));
                    })
                    .then(res => {
                        return this.sendAuthRequest({
                            ownerInfo: res.ownerInfo,
                            signedData: res.signedData,
                            caCN: caCN,
                            rememberMe: this.rememberMe,
                            keyType: 'file'
                        });
                    })
                    .then(response => {
                        if (response.data && response.data.is_logged === 1) {
                            window.location.href = this.nextUrl || '/';
                        } else {
                            this.error = this.translations.authFailed;
                            this.loading = false;
                        }
                    })
                    .catch(err => {
                        console.error("Auth error:", err);
                        this.error = (err && (err.message || err.toString())) || this.translations.authError;
                        this.loading = false;
                    });
            }
        }
    };
</script>
