// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

$('#logout_link').bind('click', function(ev) {
    ev.stopPropagation();

    if(confirm("Are you sure you want to log out?")) {
        $('#logout_form').submit();
    }
});

// @license-end
