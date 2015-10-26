// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

function initDonate() {
    // make sure any existing stripe_token is cleared
    $('#id_stripe_token').val('');

    hideshowPremiums();
    $('#donate_form input[name=premiums]').change(hideshowPremiums);
}

function hideshowPremiums() {
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

// @license-end
