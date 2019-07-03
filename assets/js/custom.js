import { saveAs } from 'file-saver';
import * as Toastr from 'toastr';

/**
 * Обновляет GET-параметр в url.
 */
function updateURLParameter(url, param, paramVal)
{
    let TheAnchor = null;
    let newAdditionalURL = "";
    let tempArray = url.split("?");
    let baseURL = tempArray[0];
    let additionalURL = tempArray[1];
    let temp = "";

    if (additionalURL)
    {
        let tmpAnchor = additionalURL.split("#");
        let TheParams = tmpAnchor[0];
            TheAnchor = tmpAnchor[1];
        if(TheAnchor)
            additionalURL = TheParams;

        tempArray = additionalURL.split("&");

        for (let i=0; i<tempArray.length; i++)
        {
            if(tempArray[i].split('=')[0] != param)
            {
                newAdditionalURL += temp + tempArray[i];
                temp = "&";
            }
        }
    }
    else
    {
        let tmpAnchor = baseURL.split("#");
        let TheParams = tmpAnchor[0];
            TheAnchor  = tmpAnchor[1];

        if(TheParams)
            baseURL = TheParams;
    }

    if(TheAnchor)
        paramVal += "#" + TheAnchor;

    let rows_txt = temp + "" + param + "=" + paramVal;
    return baseURL + "?" + newAdditionalURL + rows_txt;
}

$(function () {
    $(document).on(
        'change',
        '#filter-form input[type=checkbox]',
        function () {
            $("#filter-form").submit();
        });


    // Показать/скрыть все аналоги изобретений/полезных моделей
    $(document).on(
        'click',
        '.i_56 .show-all',
        function (e) {
            e.preventDefault();
            $(".i_56 li.more").toggleClass('hidden');
            $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
        });

    // Показать/скрыть всех заявителей
    $(document).on(
        'click',
        '.i_71 .show-all',
        function (e) {
            e.preventDefault();
            $(".i_71 span.more").toggleClass('hidden');
            $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
        });

    // Показать/скрыть всех изобретателей
    $(document).on(
        'click',
        '.i_72 .show-all',
        function (e) {
            e.preventDefault();
            $(".i_72 span.more").toggleClass('hidden');
            $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
        });

    // Показать/скрыть всех владельцев
    $(document).on(
        'click',
        '.i_73 .show-all',
        function (e) {
            e.preventDefault();
            $(".i_73 span.more").toggleClass('hidden');
            $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
        });

    // Показать/скрыть все МПК
    $(document).on(
        'click',
        '.i_51 .show-all',
        function (e) {
            e.preventDefault();
            $(".i_51 span.more").toggleClass('hidden');
            $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
        });

    // Показать/скрыть индексы МКТП
    $(document).on(
        'click',
        '.mktp-indexes .show-indexes',
        function (e) {
            e.preventDefault();
            let $this = $(this);
            $this.parents().first().find('span.more').toggleClass('hidden');
            $this.find('i').toggleClass('fa-minus').toggleClass('fa-plus');
        });

    // Выделитть (снять выделение) все документы
    $(document).on(
        'click',
        '#documents-form #select-all-documents',
        function (e) {
            var $this = $(this);
            if ($this.is(':checked')) {
                $("#documents-form input[name=cead_id]").prop('checked', true);
            } else {
                $("#documents-form input[name=cead_id]").prop('checked', false);
            }
        });

    // Обработчик события смены параметра сортировки результатов
    $(document).on(
        'change',
        '#sort_by',
        function () {
            window.location.href = updateURLParameter(window.location.href, 'sort_by', $(this).val());
        });

    // Обработчик события нажатия кнопки скачивания выписки
    $('#download-selection-btn').click(function (e) {
        e.preventDefault();
        let $btn = $(this);
        let $form = $("#selection-form");
        let oldHtml = $btn.html();
        $btn.html('<i class="fa fa-spinner g-mr-5"></i>' + gettext('Зачекайте...'));
        $btn.attr('disabled', true);

        let xhr = new XMLHttpRequest();

        let url = $form.attr("action") + '?' + $form.serialize();
        xhr.open("GET", url);
        xhr.responseType = "blob";

        xhr.onload = function () {
            if (xhr.status === 200) {
                let header = xhr.getResponseHeader('Content-Disposition');
                let startIndex = header.indexOf("filename=") + 10;
                let endIndex = header.length - 1;
                let filename = header.substring(startIndex, endIndex);
                saveAs(this.response, filename);
            } else {
                Toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
            }
            $btn.html(oldHtml);
            $btn.attr('disabled', false);
        };
        xhr.send();
    });
});
