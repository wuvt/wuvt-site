// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

var csrf_token = "{{ csrf_token() }}";

$('button.delete-button').bind('click', function(ev) {
    if(!confirm("Are you sure you want to delete this role entry?")) {
        return false;
    }

    $.ajax({
        'type': "DELETE",
        'url': $(this).closest('form').attr('action'),
        'headers': {'X-CSRFToken': csrf_token},
    }).done(function(msg) {
        csrf_token = msg['_csrf_token'];
        $(ev.currentTarget).closest('tr').fadeTo('fast', 0, function() {
            $(this).remove();
        });
    });
    return false;
});

// @license-end
