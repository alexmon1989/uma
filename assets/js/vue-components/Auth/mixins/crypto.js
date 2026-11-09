import axios from '../../../axios-config';

export const cryptoMixin = {
    props: {
        euscpUrl: {
            type: String,
            required: true
        }
    },
    methods: {
        /**
         * Динамічно завантажує бібліотеку euscp.js, якщо вона ще не завантажена,
         * та очікує на готовність глобальних об'єктів EndUser та EndUserConstants.
         */
        ensureCryptoLoaded(maxRetries = 50, interval = 100) {
            return new Promise((resolve, reject) => {
                if (window.EndUser && window.EndUserConstants) {
                    return resolve();
                }

                let script = document.getElementById('iit-euscp-script');
                if (!script) {
                    script = document.createElement('script');
                    script.id = 'iit-euscp-script';
                    script.type = 'text/javascript';
                    script.src = this.euscpUrl;
                    document.head.appendChild(script);
                }

                let retries = 0;
                const check = () => {
                    if (window.EndUser && window.EndUserConstants) {
                        resolve();
                    } else if (retries >= maxRetries) {
                        reject(new Error("Timeout loading crypto library euscp.js"));
                    } else {
                        retries++;
                        setTimeout(check, interval);
                    }
                };
                check();
            });
        },

        /**
         * Повертає стандартні налаштування для криптографічного модуля ІІТ EndUser.
         */
        getEuSettings() {
            const langMatch = window.location.pathname.match(/^\/([a-z]{2})\//);
            const lang = (langMatch && langMatch[1] === 'en') ? 'en' : 'uk';

            return {
                language: lang,
                encoding: "utf-16le",
                httpProxyServiceURL: "/auth/proxy-handler/",
                directAccess: true,
                CAs: "/certs/CAs.json",
                CACertificates: "/certs/CACertificates.p7b"
            };
        },

        /**
         * Формує FormData та відправляє POST-запит на бекенд для авторизації (/auth/login_ds/).
         */
        sendAuthRequest({ ownerInfo, signedData, caCN, rememberMe, keyType = 'file' }) {
            const postData = new FormData();
            for (let k in ownerInfo) {
                if (Object.prototype.hasOwnProperty.call(ownerInfo, k) && ownerInfo[k] !== null && ownerInfo[k] !== undefined) {
                    postData.append(k, ownerInfo[k]);
                }
            }
            postData.append('signed_data', signedData);
            postData.append('key_center_title', caCN || ownerInfo.issuerCN || ownerInfo.pszIssuerCN || '');
            postData.append('key_type', keyType || 'file');
            if (rememberMe) {
                postData.append('remember_me', '1');
            }

            const langMatch = window.location.pathname.match(/^\/([a-z]{2})\//);
            const langPrefix = langMatch ? '/' + langMatch[1] : '/uk';
            const loginUrl = `${langPrefix}/auth/login_ds/`;

            return axios.post(loginUrl, postData);
        }
    }
};
