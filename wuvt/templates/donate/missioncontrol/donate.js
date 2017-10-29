// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

var shippingMin = parseInt("{{ premiums_config.shipping_minimum }}");

initDonate();

var handler = StripeCheckout.configure({
    key: "{{ config.STRIPE_PUBLIC_KEY }}",
    image: "{{ url_for('static', filename='img/icon.png', _external=True) }}",
    token: function(token) {
        $('#id_stripe_token').val(token.id);
        $.ajax({
            'url': $('#donate_form')[0].action,
            'type': 'post',
            'data': $('#donate_form').serialize(),
        }).done(function(data) {
            $('#donate_form button[type=submit]').prop('disabled', true);

            window.location.href = "{{ url_for('donate.missioncontrol_index') }}";
        }).fail(function(data) {
            alert("There was a problem donating!");
            console.log(data);
        });
    }
});

$('#donate_form').submit(function(ev) {
    if($('#id_premiums_ship').is(':checked') && ($('#id_address_1').val().length <= 0 || $('#id_city').val().length <= 0 || $('#id_state').val().length <= 0 || $('#id_zipcode').val().length <= 0)) {
        alert("Please fill out the address fields.");
        ev.preventDefault();
        return;
    }

    if($('#id_method').val() == "stripe_missioncontrol") {
        var opts = {
            name: "{{ config.STRIPE_NAME }}",
            description: "Donate Online",
            currency: "usd",
{% if config.STRIPE_MISSIONCONTROL_EMAIL|length > 0 %}
            email: "{{ config.STRIPE_MISSIONCONTROL_EMAIL }}",
{% else %}
            email: $('#id_email').val(),
{% endif %}
            bitcoin: false,
            panelLabel: "Charge {{ '{{amount}}' }}",
        };

        var selectedPlan = $('option:selected', $('#id_plan'));

        if(selectedPlan.val().length > 0) {
            var amount = parseInt(selectedPlan.attr('data-amount'));
            if($('#id_premiums_ship').is(':checked') && amount >= shippingMin) {
                amount += parseInt("{{ premiums_config.shipping_cost }}");
            }

            // Open Checkout with options
            opts['amount'] = amount;
            handler.open(opts);
        } else if($('#id_amount').val().length > 0) {
            var amount = parseFloat($('#id_amount').val()) * 100;
            if($('#id_premiums_ship').is(':checked') && amount >= shippingMin) {
                amount += parseInt("{{ premiums_config.shipping_cost }}");
            }

            // Open Checkout with options
            opts['amount'] = amount;
            handler.open(opts);
        } else {
            alert("Please enter or a select an amount to donate.");
        }

        ev.preventDefault();
    }
});

// Close Checkout on page navigation
$(window).on('popstate', function() {
    handler.close();
});

// @license-end
