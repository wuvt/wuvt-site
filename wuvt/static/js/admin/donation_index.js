// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

$('#donations').DataTable({
    'order': [[3, 'desc']],
});

function confirm_delete(e){
    if(!confirm('Are you sure you want to reset donation stats?'))e.preventDefault();
}

// @license-end
