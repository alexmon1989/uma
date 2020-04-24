import { saveAs } from 'file-saver';

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
    let siteKey = document.querySelector("meta[name='site-key']").getAttribute("content");

    grecaptcha.execute(siteKey, {action: 'downloadfile'}).then(function (token) {
        $.ajax({
            type: 'get',
            url: '/search/get-task-info/',
            data: {'task_id': taskId, 'token': token},
            success: function (data) {
                if (data.state === 'SUCCESS') {
                    if (data.result === false) {
                        toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
                    } else {
                        toastr.success(gettext('Файл було сформовано.'));
                        saveAs(data.result, data.result.split('/').pop());
                    }
                    onSuccess(data);
                } else {
                    if (retries > 0) {
                        setTimeout(function () {
                            downloadFileAfterTaskExec(taskId, onSuccess, onError, --retries);
                        }, 1000);
                    } else {
                        toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
                        onError();
                    }
                }
            },
            error: function (data) {
                toastr.error(gettext('Виникла помилка. Будь-ласка, спробуйте пізніше.'));
                onError();
            }
        });
    });
}

/**
 * Печать элемента.
 */
function printElem(divId) {
    let content = document.getElementById(divId).cloneNode(true);
    let headHtml = document.getElementsByTagName('head')[0].innerHTML;

    // remove all <a> elements
    let elements = content.querySelectorAll('a:not(.js-fancybox)');
    [].forEach.call(elements, function(el) {
        el.remove();
    });

    elements = content.querySelectorAll(".hidden");
    [].forEach.call(elements, function(el) {
        el.classList.remove("hidden");
    });

    let myWindow = window.open('', 'Print', 'height=600,width=800');

    myWindow.document.write('<html>' + headHtml);
    myWindow.document.write('<body>' + content.innerHTML + '</body></html>');

    myWindow.document.close();
    myWindow.focus();
    setTimeout(function () {
        myWindow.print();
        myWindow.close();
    }, 1000);
    return true;
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

    // Обработчик события смены параметра сортировки результатов
    $(document).on(
        'change',
        '#show',
        function () {
            // Выставление 1-ой страницы, чтоб не показывалась страница без результатов
            var newHref =  updateURLParameter(window.location.href, 'page', 1);
            window.location.href = updateURLParameter(newHref, 'show', $(this).val());
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
        toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування файлу.'), {timeOut: 5000});
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
        toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування документу.'), {timeOut: 5000});
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
            toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування файлу.'), {timeOut: 5000});
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
            toastr.error(gettext('Не було обрано жодного документу.'));
        }
    });

    // Обработчик события нажатия на кнопку формирования и загрузки файла с результатами поиска
    // Обработчик события нажатия на кнопку формирования и загрузки файла с досутпными для всех документами
    $(document).on('click', '#search-result-download-btn, #download-shared-docs-btn', function (e) {
        e.preventDefault();
        let $this = $(this);
        $this.attr('disabled', true);
        $this.find('i').first().removeClass('fa-download').addClass('fa-spinner');
        toastr.info(gettext('Будь-ласка, зачекайте, відбувається формування файлу.'), {timeOut: 10000});

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
                },
                60
            );
        });
    });


    // Обработчик нажатия на конпку печати библиографических данных
    $(document).on('click', '#biblio-print-btn', function (e) {
        e.preventDefault();

        let content = document.getElementById('biblio-data').cloneNode(true);
        let headHtml = document.getElementsByTagName('head')[0].innerHTML;

        // Удаление ссылок, которые не являются изображениями
        let elements = content.querySelectorAll('a:not(.js-fancybox)');
        [].forEach.call(elements, function(el) {
            el.remove();
        });

        // Удаление класса hidden
        elements = content.querySelectorAll(".hidden");
        [].forEach.call(elements, function(el) {
            el.classList.remove("hidden");
        });

        // Удаление элемента kzpt-desc-short
        let element = content.querySelector(".kzpt-desc-short");
        if (element) {
            element.remove();
        }
        // Отображение элемента kzpt-desc-short
        element = content.querySelector(".kzpt-desc-full");
        if (element) {
            element.style.display = 'block';
        }

        let myWindow = window.open('', 'Print', 'height=600,width=800');

        myWindow.document.write('<html>' + headHtml);
        myWindow.document.write('<body>' + content.innerHTML + '</body></html>');

        myWindow.document.close();
        myWindow.focus();
        setTimeout(function () {
            myWindow.print();
            myWindow.close();
        }, 1000);
    });

    // Добавление/удаление объектов из избранного
    $(document).on('mouseenter', '.add-remove-favorites', function () {
        $(this).find('i').removeClass('fa-star-o').addClass('fa-star');
    }).on('mouseleave', '.add-remove-favorites', function () {
        let $this = $(this);
        if (!$this.hasClass('is-in-favorites')) {
            $this.find('i').removeClass('fa-star').addClass('fa-star-o');
        }
    }).on('click', '.add-remove-favorites', function (e) {
        e.preventDefault();
        let $favoritesTotalElem = $("#favorites-total");
        let favoritesTotalVal = parseInt($favoritesTotalElem.html());
        let $this = $(this);

        $this.toggleClass('is-in-favorites');

        if ($this.hasClass('is-in-favorites')) {
            favoritesTotalVal++;
            $this.find('i').removeClass('fa-star-o').addClass('fa-star');
            $this.attr('title', gettext('Видалити зі списку вибраних документів'));
            toastr.success(gettext('Документ було додано до списку вибраних документів.'));
        } else {
            favoritesTotalVal--;
            $this.find('i').removeClass('fa-star').addClass('fa-star-o');
            $this.attr('title', gettext('Додати до списку вибраних документів'));
            toastr.success(gettext('Документ було видалено зі списку вибраних документів.'));
        }

        $favoritesTotalElem.html(favoritesTotalVal);

        $.post('/favorites/add-or-remove', { id: $this.data('hit-id') });
    });
});