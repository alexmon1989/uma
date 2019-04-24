/**
 * Обновляет GET-параметр в url.
 */
function updateURLParameter(url, param, paramVal) {
    let newAdditionalURL = "";
    let tempArray = url.split("?");
    let baseURL = tempArray[0];
    let additionalURL = tempArray[1];
    let temp = "";
    if (additionalURL) {
        tempArray = additionalURL.split("&");
        for (let i = 0; i < tempArray.length; i++) {
            if (tempArray[i].split('=')[0] !== param) {
                newAdditionalURL += temp + tempArray[i];
                temp = "&";
            }
        }
    }

    let rows_txt = temp + "" + param + "=" + paramVal;
    return baseURL + "?" + newAdditionalURL + rows_txt;
}

$(function () {
    $filterForm = $("#filter-form");
    $filterForm.find("input[type=checkbox]").change(function () {
        $filterForm.submit();
    });

    // Показать/скрыть все аналоги изобретений/полезных моделей
    $(".i_56 .show-all").click(function (e) {
        e.preventDefault();
        $(".i_56 li.more").toggleClass('hidden');
        $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
    });

    // Показать/скрыть всех заявителей
    $(".i_71 .show-all").click(function (e) {
        e.preventDefault();
        $(".i_71 span.more").toggleClass('hidden');
        $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
    });

    // Показать/скрыть всех изобретателей
    $(".i_72 .show-all").click(function (e) {
        e.preventDefault();
        $(".i_72 span.more").toggleClass('hidden');
        $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
    });

    // Показать/скрыть всех владельцев
    $(".i_73 .show-all").click(function (e) {
        e.preventDefault();
        $(".i_73 span.more").toggleClass('hidden');
        $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
    });

    // Показать/скрыть все МПК
    $(".i_51 .show-all").click(function (e) {
        e.preventDefault();
        $(".i_51 span.more").toggleClass('hidden');
        $(this).find('i').toggleClass('fa-minus').toggleClass('fa-plus');
    });

    // Показать/скрыть индексы МКТП
    $(".mktp-indexes .show-indexes").click(function (e) {
        e.preventDefault();
        let $this = $(this);
        $this.parents().first().find('span.more').toggleClass('hidden');
        $this.find('i').toggleClass('fa-minus').toggleClass('fa-plus');
    });

    // Выделитть (снять выделение) все документы
    $("#documents-form #select-all-documents").click(function () {
        var $this = $(this);
        if ($this.is(':checked')) {
            $("#documents-form input[name=cead_id]").prop('checked', true);
        } else {
            $("#documents-form input[name=cead_id]").prop('checked', false);
        }
    });

    // Обработчик события смены параметра сортировки результатов
    $("#sort_by").change(function () {
        window.location.href = updateURLParameter(window.location.href, 'sort_by', $(this).val());
    });
});
