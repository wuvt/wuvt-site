var timerlength = 30;

var clockspan = "<span class='glyphicon glyphicon-time'></span>";
var playlisttrue = "<span class='glyphicon glyphicon-ok green'></span>";
var playlistfalse = "";

// origin: 0 if newly entered, 1 if from history
var delayinterval;
var delaybutton;

function ret_undefined() {
    return;
}

function Trackman(csrfToken, djsetId, djId, rotations) {
    this.csrfToken = csrfToken;
    this.djsetId = djsetId;
    this.djId = djId;
    this.rotations = rotations;
}

Trackman.prototype.clearForm = function(ev) {
    if(typeof ev == "undefined") {
        var inst = this;
    }
    else {
        var inst = ev.data.instance;
    }

    $(".trackman-entry input").val("");
    $(".trackman-entry input[type=checkbox]").prop("checked", false);
    $(".trackman-entry select.rotation").val(1);

    inst.searchResults = [];
    inst.updateHistory();
};

Trackman.prototype.getFormData = function() {
    return {
        "artist": $(".trackman-entry input#artist").val(),
        "title": $(".trackman-entry input#title").val(),
        "album": $(".trackman-entry input#album").val(),
        "label": $(".trackman-entry input#rlabel").val(),
        "request": $(".trackman-entry input[name=request]").prop("checked"),
        "vinyl": $(".trackman-entry input[name=vinyl]").prop("checked"),
        "new": $(".trackman-entry input[name=new]").prop("checked"),
        "rotation": $(".trackman-entry select.rotation").val(),
    };
};

Trackman.prototype.validateTrack = function(track) {
    if(track['artist'] == "") {
        alert("Must fill out the artist field");
        return false;
    }
    if(track['title'] == "") {
        alert("Must fill out the title field");
        return false;
    }
    if(track['album'] == "") {
        alert("Must fill out the album field");
        return false;
    }
    if(track['label'] == "") {
        alert("Must fill out the label field");
        return false;
    }
    return true;
};

// Autologout {{{
Trackman.prototype.initAutologout = function() {
    this.extendAutologout = false;

    $.ajax({
        url: "/trackman/api/autologout",
        dataType: "json",
        success: this.updateAutologout,
    });
    $("button#trackman-autologout").bind('click', {'instance': this},
                                         this.toggleAutologout);
};

Trackman.prototype.toggleAutologout = function(ev) {
    var inst = ev.data.instance;
    var formdata = {};
    if(inst.extendAutologout) {
        formdata['autologout'] = 'enable';
    }
    else {
        formdata['autologout'] = 'disable';
    }
    $.ajax({
        url: "/trackman/api/autologout",
        data: formdata,
        dataType: "json",
        type: "POST",
        context: inst,
        success: inst.updateAutologout,
    });
};

Trackman.prototype.updateAutologout = function(data) {
    if(data['success'] == false) {
        alert(data['error']);
        return;
    }
    if(data['autologout']) {
        $("#trackman-autologout").removeClass("active");
        this.extendAutologout = false;
    }
    else {
        $("#trackman-autologout").addClass("active");
        this.extendAutologout = true;
    }
};
// }}}

// Queue {{{
Trackman.prototype.initQueue = function() {
    this.queue = [];

    $("button#new-queue").bind('click', {'instance': this},
                               this.queueTrack);

    if(localStorage.getItem('trackman_queue')) {
        this.loadQueue();
    }
    else {
        this.saveQueue();
    }
};

Trackman.prototype.loadQueue = function() {
    var newQueue = localStorage.getItem('trackman_queue');
    this.queue = JSON.parse(newQueue);
    this.updateQueue();
};

Trackman.prototype.saveQueue = function() {
    localStorage.setItem('trackman_queue', JSON.stringify(this.queue));
};

Trackman.prototype.updateQueue = function() {
    this.clearTimer("queue");

    $("table#queue tbody tr").remove();
    for (var i = 0; i < this.queue.length; i++) {
        var result = this.queue[i];
        $("table#queue tbody").append(this.renderTrackRow({
            'id': i,
            'artist': result['artist'],
            'title': result['title'],
            'album': result['album'],
            'label': result['label'],
            'request': result['request'],
            'vinyl': result['vinyl'],
            'new': result['new'],
            'rotation': result['rotation'],
        }, 'queue'));
    }
};

Trackman.prototype.logQueued = function(element) {
    var elem = element;
    var id = element.prop("id").substring(1);
    var track = this.queue[id];
    function postLog(data) {
        if(data['success'] == false) {
            alert(data['error']);
            return;
        };
        this.queue.splice(id, 1);
        this.saveQueue();
        this.updateQueue();
        this.updatePlaylist();
    };

    // Delete it from the queue if it's there
    if(track['origin'] == 1) {
        this.logTrack(track, postLog);
    }
    else if(track['origin'] == 0) {
        this.createTrack(track, postLog);
    }
};

Trackman.prototype.clearQueue = function() {
    this.queue = [];
};

Trackman.prototype.addToQueue = function(element) {
    var id = $(element).prop("id").substring(1);
    var queueEntry = $.extend(true, {}, this.searchResults[id]);
    this.queue.push(queueEntry);
    this.clearTimer();

    this.saveQueue();
    this.updateQueue();
};

Trackman.prototype.removeFromQueue = function(element) {
    id = $(element).prop("id").substring(1);
    this.queue.splice(id, 1);

    this.saveQueue();
    this.updateQueue();
};

Trackman.prototype.queueTrack = function(ev) {
    var inst = ev.data.instance;

    var track = inst.getFormData();
    if(!inst.validateTrack(track)) {
        return false;
    }
    track['origin'] = 0;
    inst.queue.push(track);

    inst.saveQueue();
    inst.updateQueue();

    inst.clearForm();
    $('#artist').focus();
};

Trackman.prototype.queueFromJson = function(data) {
    var tracks = JSON.parse(data);
    for(i in tracks) {
        var track = tracks[i];
        if(!this.validateTrack(track)) {
            return false;
        }
        track['origin'] = 0;
        this.queue.push(track);
    }

    this.saveQueue();
    this.updateQueue();
};
// }}}

// Playlist {{{
Trackman.prototype.initPlaylist = function() {
    this.playlist = [];

    var inst = this;
    var thread = null;
    $(".trackman-entry input").keyup(function () {
        clearTimeout(thread);
        var target = $(this);
        thread = setTimeout(function(){inst.searchForm();}, 350);

    });
    $("button#new-log").bind('click', {'instance': this}, this.logNewTrack);
    $("button#clear-form").bind('click', {'instance': this}, this.clearForm);

    this.updatePlaylist();
};

Trackman.prototype.logTrack = function(track, callback) {
    $.ajax({
        url: "/trackman/api/tracklog",
        data: {
            "track_id": track['id'],
            "djset_id": djset_id,
            "vinyl":    track['vinyl'],
            "request":  track['request'],
            "new":      track['new'],
            "rotation": track['rotation'],
        },
        context: this,
        type: "POST",
        success: callback,
    });
};

Trackman.prototype.createTrack = function(track, callback) {
    $.ajax({
        url: "/trackman/api/track",
        data: { "artist": track['artist'],
                "album": track['album'],
                "title": track['title'],
                "label": track['label'],
        },
        type: "POST",
        context: this,
        success: function(data) {
            if(data['success'] == false) {
                alert(data['error']);
                return;
            }
            track['id'] = data['track_id'];
            this.logTrack(track, callback);
        },
    });
};

Trackman.prototype.logNewTrack = function(ev) {
    var inst = ev.data.instance;

    var track = inst.getFormData();
    if(!inst.validateTrack(track)) {
        return false;
    }
    track['origin'] = 0;
    function post_log(data) {
        if(data['success'] == false) {
            alert(data['error']);
            return;
        }

        inst.clearForm();
        $('#artist').focus();

        inst.updatePlaylist();
    }
    inst.createTrack(track, post_log);
};

Trackman.prototype.deleteTrack = function(element) {
    var id = $(element).prop("id");
    if(id.substring(0,1) == "p") {
        id = id.substring(1);
        $.ajax({
            url: "/trackman/api/tracklog/edit/" + id,
            type: "DELETE",
            dataType: "json",
            context: this,
            success: function(data) {
                if(data['success'] == false) {
                    alert(data['error']);
                }
                $(element).remove();
            },
        });
    }
    else {
        // This is an airlog
        // TODO: implement airlog deletion support
    }
};

Trackman.prototype.updatePlaylist = function() {
    var inst = this;
    this.fetchPlaylist(function(){
        inst.renderPlaylist();
    });
};

Trackman.prototype.fetchPlaylist = function(callback) {
    $.ajax({
        url: "/trackman/api/djset/" + djset_id,
        data: {
            "merged": true,
        },
        dataType: "json",
        context: this,
        success: function(data) {
            if(data['success'] == false) {
                alert(data['error']);
                return;
            }

            playlist = data['logs'];
            this.playlist = playlist;

            this.playlistKeyed = [];
            for(i in playlist) {
                var p = playlist[i];
                this.playlistKeyed[p['tracklog_id']] = p;
            }

            callback();
        },
    });
};

Trackman.prototype.renderRotation = function(selement, id) {
    for(r in this.rotations) {
        var opt = document.createElement('option');
        $(opt).val(r);
        $(opt).text(this.rotations[r]);
        $(selement).append(opt);
    }

    if(typeof id != "undefined") {
        $(selement).val(id);
    }
};

Trackman.prototype.renderPlaylist = function(renderRows) {
    // Empty the old playlist
    $("table#playlist tbody tr").remove();
    for(var i = 0; i < playlist.length; i++) {
        var p = playlist[i];
        // If logid is defined it's an airlog
        if('logid' in p) {
            var row = this.renderAirlogRow(p);
        }
        else {
            var row = this.renderPlaylistRow(p);
            row.attr('data-offset', i);
        }
        $("table#playlist tbody").append(row);
    }

    if(playlist.length > 0) {
        // Scroll to bottom
        var pos = $("table#playlist tbody tr:last").position();
        var scrollwindow = $("table#playlist").parent();
        scrollwindow.scrollTop(scrollwindow.scrollTop() + pos.top);
    }
};

Trackman.prototype.renderPlaylistRow = function(p) {
    return this.renderTrackRow({
        'id': p['tracklog_id'],
        'played': p['played'],
        'artist': p['track']['artist'],
        'title': p['track']['title'],
        'album': p['track']['album'],
        'label': p['track']['label'],
        'request': p['request'],
        'vinyl': p['vinyl'],
        'new': p['new'],
        'rotation': p['rotation_id']
    }, 'playlist');
};

Trackman.prototype.clearTimer = function(tableclass) {
    if(typeof tableclass != "undefined") {
        if(typeof delaybutton != "undefined") {
            if(delaybutton.parents("table").prop("id") == tableclass) {
                delaybutton.html(clockspan);
                delaybutton.off("click");
                delaybutton.bind('click', {'instance': this}, this.logTimer);
                clearInterval(delayinterval);
            }
        }
    }
    else {
        if(typeof delayinterval != "undefined") {
            clearInterval(delayinterval);
        }
        if(typeof delaybutton != "undefined") {
            delaybutton.html(clockspan);
            delaybutton.off("click");
            delaybutton.bind('click', {'instance': this}, this.logTimer);
        }
    }
    delaybutton = ret_undefined();
    delayinterval = ret_undefined();
};

Trackman.prototype.logTimer = function(ev) {
    var inst = ev.data.instance;

    inst.clearTimer();
    // Sometimes it triggers on the span itself
    if($(ev.target).prop("tagName") == "SPAN") {
        delaybutton = $(ev.target).parent();
    }
    else {
        delaybutton = $(ev.target);
    }
    delaybutton.find("span").remove();
    delaybutton.html(timerlength);
    var seconds = timerlength;
    delayinterval = setInterval(function() {
        seconds--;
        if(seconds == 0) {
            var button = delaybutton;
            inst.clearTimer();
            if(button.parents("table").prop("id") == "queue") {
                inst.logQueued(button.parents("tr.queue-row"));
            }
            else {
                inst.logSearch(button.parents("tr.search-row"));
            }
            return 0;
        }
        delaybutton.html(seconds);
    }, 1000);

    // Replace the click listener with clearTimer
    delaybutton.off("click");
    delaybutton.click(function () {inst.clearTimer()});
};
// }}}

// Search {{{
Trackman.prototype.initSearch = function() {
    this.searchResults = [];
    this.bindSearchListeners();
};

Trackman.prototype.logSearch = function(element) {
    var elem = element;
    var id = element.prop("id").substring(1);
    var track = this.searchResults[id];
    function post_log(data) {
        if(data['success'] == false) {
            alert(data['error']);
            return;
        }
        this.updatePlaylist();
    };
    this.logTrack(track, post_log);
};

Trackman.prototype.searchEdit = function(element) {
    var id = element.prop("id").substring(1);
    var track = this.searchResults[id];
    $(".trackman-entry input#artist").val(track['artist']);
    $(".trackman-entry input#title").val(track['title']);
    $(".trackman-entry input#album").val(track['album']);
    $(".trackman-entry input#rlabel").val(track['label']);
    $(".trackman-entry input[name=request]").prop("checked", track['request']);
    $(".trackman-entry input[name=vinyl]").prop("checked", track['vinyl']);
    $(".trackman-entry input[name=new]").prop("checked", track['new']);
    var track_rotation = 1;
    if(typeof track['rotation'] != "undefined") {
        track_rotation = track['rotation'];
    }
    $(".trackman-entry select.rotation").val(track_rotation);
};

Trackman.prototype.searchHistory = function() {
    var inst = this;

    $.ajax({
        url: "/trackman/api/search",
        data: this.getFormData(),
        dataType: "json",
        success: function(data) {
            if(data['success'] == false) { 
                alert(data['error']);
                return;
            }
            results = data['results'];
            inst.searchResults = [];
            for (var i = 0; i < results.length; i++) {
                results[i]['origin'] = 1;
                inst.searchResults.push(results[i])
            }
            inst.updateHistory();
        },
    });
};

Trackman.prototype.updateHistory = function() {
    this.clearTimer("search");

    // Remove old history results
    $("table#search tbody tr").remove();

    // Add new results
    for(var i = 0; i < this.searchResults.length; i++) {
        var result = this.searchResults[i];
        $("table#search tbody").append(this.renderSearchRow(i, result));
        var row = $("table#search tbody tr#s" + i);
        row.find(".request input").prop("checked", result['request']);
        row.find(".vinyl input").prop("checked", result['vinyl']);
        row.find(".new input").prop("checked", result['new']);
        this.renderRotation(row.find("select.rotation"), result['rotation']);
    }

    this.bindSearchListeners();
};

Trackman.prototype.searchForm = function() {
    var inst = this;
    $(".trackman-entry input.form-control").each(function(index) {
        if($(this).val().length >= 2) {
            inst.searchHistory();
            return false;
        }
    });
};

Trackman.prototype.bindSearchListeners = function() {
    function updateSearchResults(ev) {
        ev.data.instance.searchResults[$(ev.target).parents(".search-row").prop("id").substring(1)][$(ev.target).prop("name")] = this.checked;
    }
    function updateSearchRotation(ev) {
        ev.data.instance.searchResults[$(ev.target).parents(".search-row").prop("id").substring(1)]['rotation'] = $(ev.target).val();
    }

    $("button.search-queue").bind('click', {'instance': this}, function(ev) { 
        ev.data.instance.addToQueue($(ev.target).parents(".search-row"));
    });
    $("button.search-log").bind('click', {'instance': this}, function(ev) {
        ev.data.instance.logSearch($(ev.target).parents(".search-row"));
    });
    $("table#search input[type=checkbox]").bind('change', {'instance': this},
                                                updateSearchResults);
    $("table#search select.rotation").bind('change', {'instance': this},
                                           updateSearchRotation);
    $("table#search button.search-delay").bind('click', {'instance': this},
                                               this.logTimer);

    $("table#search button.report").bind('click', {'instance': this},
                                         function(ev) {
        search_id = $(ev.target).parents("tr").prop("id").slice(1);
        id = ev.data.instance.searchResults[search_id]['id']
        ev.data.instance.reportTrack(id);
    });
};
// }}}

Trackman.prototype.renderSearchRow = function(i, track) {
    var row = $('<tr>');
    row.addClass('search-row');
    row.attr('id', 's' + i);

    // main text entries

    var cols = ['artist', 'title', 'album', 'rlabel'];
    for(c in cols) {
        var td = $('<td>');

        var colName = cols[c];
        td.addClass(colName);

        if(colName == 'rlabel') {
            td.text(track['label']);
        }
        else {
            td.text(track[colName]);
        }

        row.append(td);
    }

    var td = $('<td>');
    td.addClass('request');
    td.html("<input type='checkbox' name='request'/>");
    row.append(td);

    var td = $('<td>');
    td.addClass('vinyl');
    td.html("<input type='checkbox' name='vinyl'/>");
    row.append(td);

    var td = $('<td>');
    td.addClass('new');
    td.html("<input type='checkbox' name='new'/>");
    row.append(td);

    var td = $('<td>');
    td.addClass('rotation');
    var newSelect = $('<select>');
    this.renderRotation(newSelect);
    td.html(newSelect);
    row.append(td);

    var td = $('<td>');
    td.addClass('text-right');
    var group = $('<div>');
    group.addClass('btn-group search-actions');

    var btn1 = $("<button class='btn btn-default btn-sm search-queue' type='button' title='Add to the queue.'><span class='glyphicon glyphicon-plus blue'></span></button>");
    group.append(btn1);
    
    var btn2 = $("<button class='btn btn-default btn-sm search-log' type='button' title='Log this track now.'><span class='glyphicon glyphicon-play'></span></button>");
    group.append(btn2);

    var btn3 = $("<button class='btn btn-default btn-sm search-delay' type='button' title='Log this track in 30 seconds.'><span class='glyphicon glyphicon-time'></span></button>");
    group.append(btn3);

    var btn4 = $("<button class='btn btn-default btn-sm report' title='Report this track for editing'><span class='glyphicon glyphicon-flag'></span></button>");
    group.append(btn4);

    td.append(group);
    row.append(td);

    return row;
};

Trackman.prototype.renderAirlogRow = function(airlog) {
    var row = $('<tr>');
    row.addClass('playlist-row airlog-row');
    row.attr('id', 'a' + airlog['id']);

    var td = $('<td>');
    td.addClass('airtime');
    td.text(airlog['played']);
    row.append(td);

    var td = $('<td>');
    td.addClass('logtype');
    td.text(airlog['logtype']);
    row.append(td);

    var td = $('<td>');
    td.addClass('logid');
    td.text(airlog['logid']);
    row.append(td);

    return row;
}

Trackman.prototype.renderTrackRow = function(track, context) {
    var row = $('<tr>');

    if(context == 'playlist') {
        row.addClass('playlist-row');
        row.attr('id', 'p' + track['id']);

        // playlist entries also get a timestamp
        var td = $('<td>');
        td.addClass('airtime');

        // Generate a date string
        var played = new Date(track['played']);
        function pad(value) {
            return ("00" + value).slice(-2);
        }
        td.text("{0}:{1}:{2}".format(pad(played.getHours()),
                                     pad(played.getMinutes()),
                                     pad(played.getSeconds())));
        row.append(td);
    }
    else {
        row.addClass('queue-row');
        row.attr('id', 'p' + track['id']);
    }

    // main text entries

    var cols = ['artist', 'title', 'album', 'rlabel'];
    for(c in cols) {
        var td = $('<td>');

        var colName = cols[c];
        td.addClass(colName);

        if(colName == 'rlabel') {
            td.text(track['label']);
        }
        else {
            td.text(track[colName]);
        }

        row.append(td);
    }

    // request/vinyl/new checkboxes

    var cols = ['request', 'vinyl', 'new'];
    for(c in cols) {
        var td = $('<td>');
        td.addClass(cols[c]);
        if(track[cols[c]] == true) {
            td.html(playlisttrue);
        }
        row.append(td);
    }

    // rotation

    var rotation_id = track['rotation'];
    if(rotation_id == null) {
        rotation_id = 1;
    }

    var td = $('<td>');
    td.addClass('rotation');
    td.attr('data-rotation-id', rotation_id);
    td.text(this.rotations[rotation_id]);
    row.append(td);

    // buttons

    var td = $('<td>');
    td.addClass('text-right');
    var group = $('<div>');
    group.addClass('btn-group');
    td.append(group);
    row.append(td);

    if(context == 'playlist') {
        group.addClass('playlist-actions');

        var editBtn = $("<button class='btn btn-default btn-sm playlist-edit' title='Edit this track'><span class='glyphicon glyphicon-pencil'></span></button>");
        editBtn.bind('click', {'instance': this, 'context': 'playlist'},
                     this.inlineEditTrack);
        group.append(editBtn);

        var reportBtn = $("<button class='btn btn-default btn-sm report' title='Report this track for editing'><span class='glyphicon glyphicon-flag'></span></button>");
        reportBtn.bind('click', {'instance': this}, function(ev) {
            playlist_id = $(ev.target).parents("tr").prop("id").slice(1);
            tracklog = $.grep(playlist, function(e){ return e.tracklog_id == playlist_id;})[0];
            id = tracklog['track_id'];
            ev.data.instance.reportTrack(id);
        });
        group.append(reportBtn);

        var deleteBtn = $("<button class='btn btn-danger btn-sm playlist-delete' title='Delete this track from playlist'><span class='glyphicon glyphicon-trash'></span></button>");
        deleteBtn.bind('click', {'instance': this}, function(ev) {
            ev.data.instance.deleteTrack(row);
        });
        group.append(deleteBtn);
    }
    else if(context == 'queue') {
        group.addClass('queue-actions');

        var logBtn = $("<button class='btn btn-default btn-sm queue-log' type='button' title='Log this track now!'><span class='glyphicon glyphicon-play'></span></button>");
        logBtn.bind('click', {'instance': this}, function(ev) {
            ev.data.instance.logQueued(row);
            ev.data.instance.clearForm();
            $('#artist').focus();
        });
        group.append(logBtn);

        var logDelayBtn = $("<button class='btn btn-default btn-sm queue-delay' type='button' title='Log this track in 30 seconds.'><span class='glyphicon glyphicon-time'></span></button>");
        logDelayBtn.bind('click', {'instance': this}, this.logTimer);
        group.append(logDelayBtn);

        var editBtn = $("<button class='btn btn-default btn-sm queue-edit' title='Edit this track'><span class='glyphicon glyphicon-pencil'></span></button>");
        editBtn.bind('click', {'instance': this, 'context': 'queue'},
                     this.inlineEditTrack);
        group.append(editBtn);

        var deleteBtn = $("<button class='btn btn-danger btn-sm queue-delete' type='button' title='Delete this track from queue'><span class='glyphicon glyphicon-trash'></span></button>");
        deleteBtn.bind('click', {'instance': this}, function(ev) {
            ev.data.instance.removeFromQueue(row);
        });
        group.append(deleteBtn);
    }

    return row;
};

Trackman.prototype.inlineEditTrack = function(ev) {
    var inst = ev.data.instance;
    var context = ev.data.context;
    var row = $(ev.target).parents('tr');
    var id = row.prop("id").slice(1);

    function serializeTrackRow() {
        return {
            'artist': $('.artist input', row).val(),
            'title': $('.title input', row).val(),
            'album': $('.album input', row).val(),
            'label': $('.rlabel input', row).val(),
            'request': $('.request input', row).prop('checked'),
            'vinyl': $('.vinyl input', row).prop('checked'),
            'new': $('.new input', row).prop('checked'),
            'rotation': $('.rotation select', row).val(),
        };
    }

    function startEditBtn(editBtn, cancelCallback) {
        editBtn.removeClass('btn-default');
        editBtn.addClass('btn-success');
        editBtn.attr('title', "Save this track");
        $('span.glyphicon', editBtn).removeClass('glyphicon-pencil');
        $('span.glyphicon', editBtn).addClass('glyphicon-ok');

        var cancelBtn = $('<button>');
        cancelBtn.addClass('btn btn-default btn-sm cancel-edit');
        var cancelGlyph = $('<span>');
        cancelGlyph.addClass('glyphicon glyphicon-remove');
        cancelBtn.html(cancelGlyph);
        editBtn.after(cancelBtn);

        cancelBtn.bind('click', {'instance': inst, 'id': id}, cancelCallback);
    }

    if(context == 'playlist') {
        if(row.hasClass('editing')) {
            var track = serializeTrackRow();
            if(!inst.validateTrack(track)) {
                row.addClass('danger');
                return false;
            }

            $.ajax({
                url: "/trackman/api/tracklog/edit/" + id,
                data: {
                    "artist":   track['artist'],
                    "album":    track['album'],
                    "title":    track['title'],
                    "label":    track['label'],
                    "vinyl":    track['vinyl'],
                    "request":  track['request'],
                    "new":      track['new'],
                    "rotation": track['rotation'],
                },
                dataType: "json",
                type: "POST",
                success: function(data) {
                    if(data['success'] == false) {
                        alert(data['error']);
                        return;
                    }

                    inst.fetchPlaylist(function() {
                        row.replaceWith(inst.renderPlaylistRow(inst.playlistKeyed[id]));
                    });
                },
            });
            return;
        }

        startEditBtn($('button.playlist-edit', row), function(ev) {
            row.replaceWith(inst.renderPlaylistRow(inst.playlistKeyed[id]));
        });
        $('button.report', row).attr('disabled', 'disabled');
        $('button.playlist-delete', row).attr('disabled', 'disabled');
    }
    else if(context == 'queue') {
        if(row.hasClass('editing')) {
            inst.clearTimer('queue');

            var track = serializeTrackRow();
            if(!inst.validateTrack(track)) {
                row.addClass('danger');
                return false;
            }

            track['id'] = id;
            track['origin'] = 0;
            inst.queue[id] = track;

            row.replaceWith(inst.renderTrackRow(track, 'queue'));
            inst.saveQueue();
            return;
        }

        startEditBtn($('button.queue-edit', row), function(ev) {
            var inst = ev.data.instance;
            var track = inst.queue[id];
            track['id'] = id;
            row.replaceWith(inst.renderTrackRow(track, 'queue'));
        });
        $('button.queue-log', row).attr('disabled', 'disabled');
        $('button.queue-delay', row).attr('disabled', 'disabled');
        $('button.queue-delete', row).attr('disabled', 'disabled');
    }

    function transformToInput(obj) {
        var input = $('<input>');
        input.attr('type', 'input');
        input.addClass('form-control');
        input.addClass('input-sm');

        input.val($(obj).text());

        $(obj).html(input);
    }

    function transformToCheckbox(obj) {
        var input = $('<input>');
        input.attr('type', 'checkbox');
        input.attr('checked', $(obj).html().length > 0);
        $(obj).html(input);
    }

    row.addClass('editing');
    transformToInput($('.artist', row));
    transformToInput($('.title', row));
    transformToInput($('.album', row));
    transformToInput($('.rlabel', row));
    transformToCheckbox($('.request', row));
    transformToCheckbox($('.vinyl', row));
    transformToCheckbox($('.new', row));

    var newSelect = $('<select>');
    inst.renderRotation(newSelect, $('.rotation', row).attr('data-rotation-id'));
    $('.rotation', row).html(newSelect);
};

Trackman.prototype.reportTrack = function(id) {
    url = "/trackman/report/" + dj_id + "/" + id;
    var report_win = window.open(url, "reportWindow", "height=600,width=1200");
};

Trackman.prototype.init = function() {
    var inst = this;
    $('#trackman_logout_btn').bind('click', {}, function() {
        var email = ($('#id_email_playlist:checked').val() == "on") ? 'true' : 'false';
        $("#trackman_logout_form input[name='email_playlist']").val(email);

        inst.clearQueue();
        inst.saveQueue();

        $('#trackman_logout_form').submit();
    });

    this.initAutologout();
    this.initQueue();
    this.initPlaylist();
    this.initSearch();
};
