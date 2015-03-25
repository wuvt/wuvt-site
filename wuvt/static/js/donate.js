function init_donate() {
    // make sure any existing stripe_token is cleared
    $('#id_stripe_token').val('');

    hideshow_premiums();
    $('#donate_form input[name=premiums]').change(hideshow_premiums);
}

function hideshow_premiums() {
    if($('#id_premiums_pickup').is(':checked')) {
        $('#premium_fields').show('fast');
        $('#shipping_fields').hide('fast');
    }
    else if($('#id_premiums_ship').is(':checked')) {
        $('#premium_fields').show('fast');
        $('#shipping_fields').show('fast');
    }
    else {
        $('#premium_fields').hide('fast');
        $('#shipping_fields').hide('fast');
    }
}

