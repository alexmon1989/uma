// Styles
import '../vendor/bootstrap/bootstrap.min.css';
import '../vendor/icon-awesome/css/font-awesome.min.css';
import '../vendor/icon-line/css/simple-line-icons.css';
import '../vendor/icon-etlinefont/style.css';
import '../vendor/icon-line-pro/style.css';
import '../vendor/hs-megamenu/src/hs.megamenu.css';
import '../vendor/hamburgers/hamburgers.min.css';
import '../vendor/icon-hs/style.css';
import '../vendor/animate.css';
import '../vendor/chosen/chosen.css';
import '../vendor/fancybox/jquery.fancybox.min.css';
import '../../node_modules/toastr/build/toastr.css';
import '../include/scss/unify.scss'

// Scripts
import '../vendor/jquery/jquery.min.js';
import '../vendor/jquery-migrate/jquery-migrate.min.js';
import '../vendor/popper.min.js';
import '../vendor/bootstrap/bootstrap.min.js';
import '../vendor/chosen/chosen.jquery.js';
import '../vendor/fancybox/jquery.fancybox.min.js';

import '../vendor/hs-megamenu/src/hs.megamenu.js';
import '../js/hs.core.js';
import '../js/components/hs.header.js';
import '../js/components/hs.dropdown.js';
import '../js/components/hs.select.js';
import '../js/components/hs.popup.js';
import '../js/helpers/hs.hamburgers.js';
import './custom.js';

$(document).on('ready', function () {
    // initialization of HSDropdown component
    $.HSCore.components.HSDropdown.init($('[data-dropdown-target]'));

    // initialization of custom select
    $.HSCore.components.HSSelect.init('.js-custom-select');

    // initialization of popups
    $.HSCore.components.HSPopup.init('.js-fancybox');

    // initialization of popovers
    $('[data-toggle="popover"]').popover();
});

$(window).on('load', function () {
    // initialization of header
    $.HSCore.components.HSHeader.init($('#js-header'));
    $.HSCore.helpers.HSHamburgers.init('.hamburger');

    // initialization of HSMegaMenu component
    $('.js-mega-menu').HSMegaMenu({
        event: 'hover',
        pageContainer: $('.container'),
        breakpoint: 991
    });
});