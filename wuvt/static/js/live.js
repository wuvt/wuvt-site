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
            addDJLink('#current_dj', msg['tracklog']);

            if($('#last15tracks').length) {
                updateLast15(msg['tracklog']);
            }
        }
    };
}

function addDJLink(elem, tracklog) {
    if(tracklog['dj_visible']) {
        var link = document.createElement('a');
        link.href = '/playlists/dj/' + tracklog['dj_id'];
        $(link).text(tracklog['dj']);
        makeAjaxLink(link);

        $(elem).html(link);
    }
    else {
        $(elem).text(tracklog['dj']);
    }
}

function updateLast15(tracklog) {
    if($('#last15tracks tbody tr').length >= 15) {
        // remove last item if already 15 tracks
        $('#last15tracks tbody tr:last-child').remove();
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
    addDJLink(td, tracklog);
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

    $('#last15tracks tbody').prepend(tr);
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

        if($('#playlists_by_date').length) {
            var p = new PlaylistsByDate('#playlists_by_date');
            p.init();
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

function initAjaxLinks() {
    makeAjaxLink($('#nowplaying a'));
    makeAjaxLink($('header #mainheader h1 a'));
    $.each($('#bubble a'), function(i, item){makeAjaxLink(item);});
    $.each($('nav a'), function(i, item){makeAjaxLink(item);});
    $.each($('#content a'), function(i, item){makeAjaxLink(item);});
    $.each($('body > footer a'), function(i, item){makeAjaxLink(item);});

    window.onpopstate = function(ev) {
        loadPage(ev.state.path);
    };
}
