var shipping_minimum = parseInt("{{ config.DONATE_SHIPPING_MINIMUM }}") * 100;

alert(shipping_minimum);

init_donate();

var handler = StripeCheckout.configure({
    key: "{{ config.STRIPE_PUBLIC_KEY }}",
    image: '/static/img/icon.png',
    token: function(token) {
        $('#id_stripe_token').val(token.id);
        $.ajax({
            'url': $('#donate_form')[0].action,
            'type': 'post',
            'data': $('#donate_form').serialize(),
        }).done(function(data) {
            var path = "{{ url_for('donate.thanks') }}";
            window.history.replaceState({'path': path}, "Donate Online", path);
            loadPage(path);
        }).fail(function(data) {
            alert("There was a problem donating!");
            console.log(data);
        });
    }
});

$('#donate_form').submit(function(ev) {
    var amount = parseFloat($('#id_amount').val()) * 100;
    if($('#id_premiums_ship').is(':checked') && amount >= shipping_minimum) {
        amount += parseInt("{{ config.DONATE_SHIPPING_COST }}") * 100;
    }

    // Open Checkout with further options
    handler.open({
        name: "{{ config.STRIPE_NAME }}",
        description: "Donate Online",
        amount: amount,
        currency: "usd",
        panelLabel: "Pay {{ '{{amount}}' }}",
        email: $('#id_email').val(),
        bitcoin: true,
    });

    ev.preventDefault();
});

// Close Checkout on page navigation
$(window).on('popstate', function() {
    handler.close();
});
