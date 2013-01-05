function wuvtLive(liveurl) {
    var source = new EventSource(liveurl);
    source.onmessage = function(ev) {
        msg = JSON.parse(ev.data);
        if(msg['event'] == "track_change") {
            $('#current_track').text(msg['track']['artist'] + " - " +
                    msg['track']['title']);
            $('#current_dj').text(msg['track']['dj']);

            if($('#trackable')) {
                updateLast15(msg['track']);
            }
        }
    };
}

function updateLast15(track) {
    if($('#tracktable tbody tr').length >= 15) {
        // remove last item if already 15 tracks
        $('#tracktable tbody tr:last-child').remove();
    }

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

function makeAjaxLink(item) {
    if($(item).attr('href').charAt(0) == '#') {
        return;
    }

    $(item).click(function(ev) {
        path = ev.target.href;
        window.history.pushState({'path': path}, item.innerText, path);
        loadPage(path);

        return false;
    });
}

function loadPage(path) {
    $.ajax({
        'url': path,
        'dataType': 'html',
    }).done(function(data) {
        doc = $('<div>').append($.parseHTML(data));
        $('title').text(doc.find('title').text());
        $('#content').html(doc.find('#content > *'));
        $.each($('#content a'), function(i, item){makeAjaxLink(item);});
    });
}
