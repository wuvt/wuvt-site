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

function wuvtLiveLast15(liveurl) {
    var source = new EventSource(liveurl);
    source.onmessage = function(ev) {
        msg = JSON.parse(ev.data);
        if(msg['event'] == "track_change") {
            $('#current_track').text(msg['track']['artist'] + " - " +
                    msg['track']['title']);
            $('#current_dj').text(msg['track']['dj']);

            var track = msg['track'];
            $('#tracktable tbody tr:last-child').remove();

            var tr = document.createElement('tr');

            var td = document.createElement('td');
            var playtime = track['datetime'].split(' ')[1];
            playtime = playtime.split('.')[0];
            $(td).text(playtime);
            $(tr).append(td);

            var td = document.createElement('td');
            if(track['new'] == "true") {
                $(td).text("NEw");
            }
            $(tr).append(td);

            var td = document.createElement('td');
            $(td).text(track['artist'] + " - " + track['title']);
            $(tr).append(td);

            var td = document.createElement('td');
            $(td).text(track['album']);
            $(tr).append(td);

            var td = document.createElement('td');
            $(td).text(track['dj']);
            $(tr).append(td);

            var td = document.createElement('td');
            if(track['request'] == "true") {
                $(td).text("REQ");
            }
            $(tr).append(td);

            var td = document.createElement('td');
            if(track['vinyl'] == "true") {
                $(td).text("VIN");
            }
            $(tr).append(td);

            $('#tracktable tbody').prepend(tr);
        }
    };
}
