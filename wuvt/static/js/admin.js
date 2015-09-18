$('#logout_link').bind('click', function(ev) {
    ev.stopPropagation();

    if(confirm("Are you sure you want to log out?")) {
        $('#logout_form').submit();
    }
});
