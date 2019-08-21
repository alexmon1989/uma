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

function downloadFileAfterTaskExec(taskId, onSuccess, onError, retries=20) {
    $.ajax({
        type: 'get',
        url: '/search/get-task-info/',
        data: {'task_id': taskId},
        success: function (data) {
            if (data.state === 'SUCCESS') {
                if (data.result === false) {
                    Toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
                } else {
                    Toastr.success(gettext('Файл було сформовано.'));
                    saveAs(data.result, data.result.split('/').pop());
                }
                onSuccess(data);
            } else {
                if (retries > 0) {
                    setTimeout(function () {
                        downloadFileAfterTaskExec(taskId, onSuccess, onError, --retries);
                    }, 1000);
                } else {
                    Toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
                    onError();
                }
            }
        },
        error: function (data) {
            Toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
            onError();
        }
    });
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

    // Показать/скрыть описание КЗПТ
    $(document).on(
        'click',
        '.kzpt-desc-short a.show',
        function (e) {
            e.preventDefault();
            $(".kzpt-desc-short").hide();
            $(".kzpt-desc-full").fadeIn();
        });
    $(document).on(
        'click',
        '.kzpt-desc-full a.hide',
        function (e) {
            e.preventDefault();
            $(".kzpt-desc-full").hide();
            $(".kzpt-desc-short").fadeIn();
        });

    // Обработчик события отправки формы формирования выписки
    $(document).on('submit', '#selection-form', function (e) {
        e.preventDefault();
        let $form = $(this);
        Toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування файлу.'), {timeOut: 5000});
        $form.find('button[type=submit]')
            .attr('disabled', true)
            .find('i').first()
            .removeClass('fa-download')
            .addClass('fa-spinner');
        $.getJSON($form.attr('action'), $form.serialize(), function (data) {
            downloadFileAfterTaskExec(
                data.task_id,
                function () {
                    $form.find('button[type=submit]')
                        .removeAttr('disabled')
                        .find('i').first()
                        .removeClass('fa-spinner')
                        .addClass('fa-download');
                    },
                function () {
                    $form.find('button[type=submit]')
                        .removeAttr('disabled')
                        .find('i').first()
                        .removeClass('fa-spinner')
                        .addClass('fa-download');
                });
        });
    });

    // Обработчтк события нажатия на кнопку формирования ссылки на документ
    $(document).on('click', '#documents-form button.download-doc', function (e) {
        e.preventDefault();
        let $this = $(this);
        $this.attr('disabled', true);
        $this.find('i').first().removeClass('fa-download').addClass('fa-spinner');
        Toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування документу.'), {timeOut: 5000});
        $.getJSON($this.data('task-create-url'), function (data) {
            downloadFileAfterTaskExec(
                data.task_id,
                function (data) {
                    if (data.result === false) {
                        $this.removeAttr('disabled')
                            .find('i').first()
                            .removeClass('fa-spinner')
                            .addClass('fa-download');
                    } else {
                        $this.removeClass('btn-primary')
                            .addClass('btn-success')
                            .removeAttr('disabled')
                            .attr('title', gettext('Відкрити'))
                            .find('i').first()
                            .removeClass('fa-spinner')
                            .addClass('fa-external-link btn-success');

                        $this.attr('onclick', '').unbind('click').click(function (e) {
                            e.preventDefault();
                            e.stopPropagation();
                            saveAs(data.result, data.result.split('/').pop());
                        });
                    }
                },
                function () {
                    $this.removeAttr('disabled')
                        .find('i').first()
                        .removeClass('fa-spinner')
                        .addClass('fa-download');
                });
        });
    });

    // Обработчик события нажатия на кнопку загрузки архива с документами
    $(document).on('submit', '#documents-form', function (e) {
        e.preventDefault();
        let $form = $(this);
        // Проверка стоит ли галочка хотя бы на одном документе
        if ($("input[name='cead_id']").filter(':checked').length > 0) {
            Toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування файлу.'), {timeOut: 5000});
            $form.find('button[type=submit]')
                .attr('disabled', true)
                .find('i').first()
                .removeClass('fa-download')
                .addClass('fa-spinner');

            $.post($form.attr('action'), $form.serialize(), function (data) {
                downloadFileAfterTaskExec(
                    data.task_id,
                    function () {
                        $form.find('button[type=submit]')
                            .removeAttr('disabled')
                            .find('i').first()
                            .removeClass('fa-spinner')
                            .addClass('fa-download');
                    },
                    function () {
                        $form.find('button[type=submit]')
                            .removeAttr('disabled')
                            .find('i').first()
                            .removeClass('fa-spinner')
                            .addClass('fa-download');
                    });
            });
        } else {
            Toastr.error(gettext('Не було обрано жодного документу.'));
        }
    });

    // Обработчик события нажатия на кнопку формирования и загрузки файла с результатами поиска
    // Обработчик события нажатия на кнопку формирования и загрузки файла с досутпными для всех документами
    $(document).on('click', '#search-result-download-btn, #download-shared-docs-btn', function (e) {
        e.preventDefault();
        let $this = $(this);
        $this.attr('disabled', true);
        $this.find('i').first().removeClass('fa-download').addClass('fa-spinner');
        Toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування файлу.'), {timeOut: 10000});

        $.getJSON($this.data('task-create-url'), function (data) {
            downloadFileAfterTaskExec(
                data.task_id,
                function () {
                    $this.removeAttr('disabled')
                        .find('i').first()
                        .removeClass('fa-spinner')
                        .addClass('fa-download');
                },
                function () {
                    $this.removeAttr('disabled')
                        .find('i').first()
                        .removeClass('fa-spinner')
                        .addClass('fa-download');
                });
        });
    });
});