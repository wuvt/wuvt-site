var p = new PlaylistsByDate('#playlists_by_date');
p.init();

$(document).on('pageChange', function() {
    if($('#playlists_by_date').length) {
        var p = new PlaylistsByDate('#playlists_by_date');
        p.init();
    }
});
