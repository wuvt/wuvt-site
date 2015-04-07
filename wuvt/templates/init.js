wuvtLive("{{ url_for('livestream') }}");
initAjaxLinks();
initPlayer();
initLocalDates();

$(document).on('pageChange', function() {
    if($('#playlists_by_date').length) {
        var p = new PlaylistsByDate('#playlists_by_date');
        p.init();
    }
});
