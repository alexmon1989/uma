$(function () {
    var $ca = $("#id_ca");

    var onCaChange = function () {
        var pk = $ca.find('option:selected').val();
        var $id_cert_file = $("#id_cert_file");
        var $form_group = $id_cert_file.closest('.form-group');

        if (pk) {
            $.getJSON('/auth/get_ca_data/' + pk, function (data) {
                if (!data.cmpAddress) {
                    $id_cert_file.attr("required", true);
                    $form_group.show();
                } else {
                    $id_cert_file.attr("required", false);
                    $form_group.hide();
                }
            });
        } else {
            $id_cert_file.attr("required", false);
            $form_group.hide();
        }
    };

    onCaChange();

    $ca.change(onCaChange)
});
