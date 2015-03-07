var liveReconnectTimer;

function wuvtLive(liveurl) {
    if(typeof EventSource == 'undefined') {
        // cannot use server-sent events, boo
        return;
    }

    var source = new EventSource(liveurl);
    source.onmessage = function(ev) {
        msg = JSON.parse(ev.data);
        if(msg['event'] == "track_change") {
            var track = msg['tracklog']['track'];
            $('#current_track').text(track['artist'] + " - " +
                    track['title']);
            $('#current_dj').text(msg['tracklog']['dj']);

            if($('#tracktable')) {
                updateLast15(msg['tracklog']);
            }
        }
    };
    source.onerror = function(e) {
        if(liveReconnectTimer == null) {
            // attempt to reconnect after 15 seconds
            liveReconnectTimer = setTimeout(function() {
                liveReconnectTimer = null;
                wuvtLive(liveurl);
            }, 15000);
        }
    };
}

function updateLast15(tracklog) {
    if($('#tracktable tbody tr').length >= 15) {
        // remove last item if already 15 tracks
        $('#tracktable tbody tr:last-child').remove();
    }

    function pad(value) {
        return ("00" + value).slice(-2);
    }

    var track = tracklog['track'];
    var tr = document.createElement('tr');

    var td = document.createElement('td');
    var played = new Date(tracklog['played']);
    $(td).text("{0}:{1}:{2}".format(pad(played.getHours()),
                                    pad(played.getMinutes()),
                                    pad(played.getSeconds())));
    $(tr).append(td);

    var td = document.createElement('td');
    if(tracklog['new'] == true) {
        var span = document.createElement('span');
        span.className = "glyphicon glyphicon-fire new-track";
        $(td).append(span);
    }
    $(tr).append(td);

    var td = document.createElement('td');
    $(td).text(track['artist']);
    $(tr).append(td);

    var td = document.createElement('td');
    $(td).text(track['title']);
    $(tr).append(td);

    var td = document.createElement('td');
    $(td).text(track['album']);
    $(tr).append(td);

    var td = document.createElement('td');
    $(td).text(tracklog['dj']);
    $(tr).append(td);

    var td = document.createElement('td');
    if(tracklog['request'] == true) {
        var span = document.createElement('span');
        span.className = "glyphicon glyphicon-earphone";
        $(td).append(span);
    }
    $(tr).append(td);

    var td = document.createElement('td');
    if(tracklog['vinyl'] == true) {
        var span = document.createElement('span');
        span.className = "glyphicon glyphicon-cd";
        $(td).append(span);
    }
    $(tr).append(td);

    $('#tracktable tbody').prepend(tr);
}

function makeAjaxLink(item) {
    var absoluteRegex = new RegExp("^([a-z]+://|//)");
    var domainRegex = new RegExp(location.host);
    var staticRegex = new RegExp("/static/");
    var href = $(item).attr('href');

    if(!href || href.charAt(0) == '#' || staticRegex.test(href) ||
       (absoluteRegex.test(href) && !domainRegex.test(href))) {
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
        var doc = $('<div>').append($.parseHTML(data));
        $('title').text(doc.find('title').text());
        $('#side_primary').html(doc.find('#side_primary > *'));
        $('#content').html(doc.find('#content > *'));

        $.each($('#side_primary a'), function(i, item){makeAjaxLink(item);});
        $.each($('#content a'), function(i, item){makeAjaxLink(item);});

        // build date picker
        if($('#datepicker')) {
            $('#datepicker').datepicker({
                'dateFormat': "yy/mm/dd",
                'minDate': "2007/01/01",
                'maxDate': 0,
                'changeMonth': true,
                'changeYear': true,
                'prevText': "«",
                'nextText': "»",
                'onSelect': function(dt) {
                    loadPage("/playlists/date/" + dt);
                },
            });
        }
    }).fail(function(data) {
        var doc = $('<div>').append($.parseHTML(data.responseText));
        $('title').text(doc.find('title').text());
        $('#side_primary').html(doc.find('#side_primary > *'));
        $('#content').html(doc.find('#content > *'));

        $.each($('#side_primary a'), function(i, item){makeAjaxLink(item);});
        $.each($('#content a'), function(i, item){makeAjaxLink(item);});
    });
}
