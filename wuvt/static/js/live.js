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

    var played = moment(tracklog['played']);
    $(td).text(played.format('HH:mm:ss'));
    $(td).attr('title', played.format('LLLL'));
    $(tr).append(td);

    var td = document.createElement('td');
    if(tracklog['new'] == true) {
        var span = document.createElement('span');
        span.className = "glyphicon glyphicon-fire new-track";
        span.title = "New";
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
        span.title = "Request";
        $(td).append(span);
    }
    $(tr).append(td);

    var td = document.createElement('td');
    if(tracklog['vinyl'] == true) {
        var span = document.createElement('span');
        span.className = "glyphicon glyphicon-cd";
        span.title = "Vinyl";
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
        path = $(this).attr('href');
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

        initLocalDates();
    }).fail(function(data) {
        var doc = $('<div>').append($.parseHTML(data.responseText));
        $('title').text(doc.find('title').text());
        $('#side_primary').html(doc.find('#side_primary > *'));
        $('#content').html(doc.find('#content > *'));

        $.each($('#side_primary a'), function(i, item){makeAjaxLink(item);});
        $.each($('#content a'), function(i, item){makeAjaxLink(item);});

        initLocalDates();
    });
}

function progressTick() {
    var pageWidth = $('#progress_bar').offsetParent().width();
    var dist = Math.floor((Math.random() + 1) * 10);
    var newWidth = $('#progress_bar').width() + dist;
    if(newWidth / pageWidth < 1) {
        $('#progress_bar').width(newWidth);
    }
    else {
        $('#progress_bar').width('0.1%');
    }
}

function initProgressBar() {
    var progress = document.createElement('div');
    progress.id = 'progress_bar';
    $('body').append(progress);

    var progressTimer = setInterval(progressTick, 100);

    $(document).bind('ajaxStart', function() {
        clearInterval(progressTimer);
        progressTimer = setInterval(progressTick, 100);

        $('#progress_bar').width('0.1%');
        $('#progress_bar').fadeIn('fast');
    }).bind('ajaxComplete', function() {
        clearInterval(progressTimer);

        $('#progress_bar').width('100%');
        $('#progress_bar').fadeOut('fast');
    });

    $(window).bind('load', function() {
        clearInterval(progressTimer);

        $('#progress_bar').width('100%');
        $('#progress_bar').fadeOut('fast');
    });
}

function initAjaxLinks() {
    initProgressBar();

    makeAjaxLink($('#nowplaying a'));
    makeAjaxLink($('header #mainheader h1 a'));
    makeAjaxLink($('#radiothon_banner a'));
    $.each($('#bubble a'), function(i, item){makeAjaxLink(item);});
    $.each($('nav a'), function(i, item){makeAjaxLink(item);});
    $.each($('#content a'), function(i, item){makeAjaxLink(item);});
    $.each($('body > footer a'), function(i, item){makeAjaxLink(item);});

    // replace state in history, so going back to the first page works
    window.history.replaceState({'path': location.pathname}, window.title,
                                location.pathname);

    window.onpopstate = function(ev) {
        loadPage(ev.state.path);
    };
}

function initLocalDates() {
    $('time').each(function() {
        var datestr = $(this).attr('datetime');
        var format = $(this).attr('data-format');
        var m = moment(datestr);
        if(m.isValid()) {
            $(this).text(m.format(format));
            $(this).attr('title', m.format('LLLL'));
        }
    });
}
