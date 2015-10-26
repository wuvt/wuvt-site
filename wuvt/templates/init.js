// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

Pace.ignore(wuvtLive("{{ url_for('livestream') }}"));
initAjaxLinks();
initPlayer();
initLocalDates();

$(document).on('pageChange', function() {
    if($('#playlists_by_date').length) {
        var p = new PlaylistsByDate('#playlists_by_date');
        p.init();
    }
});

// @license-end
