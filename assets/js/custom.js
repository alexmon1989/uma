$(function () {
    $filterForm = $("#filter-form");
    $filterForm.find("input[type=checkbox]").change(function () {
        $filterForm.submit();
    });
});