import axios from 'axios'

/**
 * Config global for axios/django
 */
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

export default axios
