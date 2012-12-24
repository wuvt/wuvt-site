function wuvtLive(liveurl) {
    var source = new EventSource(liveurl);
    source.onmessage = function(ev) {
        msg = JSON.parse(ev.data);
        if(msg['event'] == "track_change") {
            $('#current_track').text(msg['track']['artist'] + " - " +
                    msg['track']['title']);
            $('#current_dj').text(msg['track']['dj']);
        }
    };
}
