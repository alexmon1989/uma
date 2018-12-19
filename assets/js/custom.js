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

    // Выделитть (снять выделение) все документы
    $("#documents-form #select-all-documents").click(function () {
        var $this = $(this);
        if ($this.is(':checked')) {
            $("#documents-form input[name=cead_id]").prop('checked', true);
        } else {
            $("#documents-form input[name=cead_id]").prop('checked', false);
        }
    });
});