// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

/* Facebook Pixel Code */
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');

fbq('init', '492011194322828');
fbq('track', "PageView");
fbq('track', 'InitiateCheckout');
/* End Facebook Pixel Code */

var shippingMin = parseInt("{{ config.DONATE_SHIPPING_MINIMUM }}") * 100;

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

            var path = "{{ url_for('donate.thanks') }}";
            window.history.replaceState({'path': path}, "Donate Online", path);
            loadPage(path);
        }).fail(function(data) {
            updatePage($.parseHTML(data.responseText, document, true));
        });
    }
});

$('#donate_loading_message').hide('fast');
$('#donate_form').show('fast');

$('#donate_form').submit(function(ev) {
    var opts = {
        name: "{{ config.STRIPE_NAME }}",
        description: "Donate Online",
        currency: "usd",
        email: $('#id_email').val(),
    };

    if($('#id_plan').length > 0) {
        var amount = parseInt($('option:selected', $('#id_plan')).attr('data-amount'));
        if($('#id_premiums_ship').is(':checked') && amount >= shippingMin) {
            amount += parseInt("{{ config.DONATE_SHIPPING_COST }}") * 100;
        }

        // Open Checkout with options
        opts['amount'] = amount;
        opts['bitcoin'] = false;
        opts['panelLabel'] = "Pay {{ '{{amount}}' }}";
        handler.open(opts);
    } else if($('#id_amount').length > 0) {
        var amountStr = $('#id_amount').val().replace(/^[\s\$]+|\s+/g, '');
        var amount = parseFloat(amountStr) * 100;
        if($('#id_premiums_ship').is(':checked') && amount >= shippingMin) {
            amount += parseInt("{{ config.DONATE_SHIPPING_COST }}") * 100;
        }

        // Open Checkout with options
        opts['amount'] = amount;
        opts['bitcoin'] = true;
        opts['panelLabel'] = "Pay {{ '{{amount}}' }}";
        handler.open(opts);
    } else {
        alert("Please enter or a select an amount to donate.");
    }

    ev.preventDefault();
});

// Close Checkout on page navigation
$(window).on('popstate', function() {
    handler.close();
});

// @license-end
