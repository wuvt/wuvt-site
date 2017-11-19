// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL-v3.0

var timerlength = 30;

var clockspan = "<span class='glyphicon glyphicon-time'></span>";
var playlisttrue = "<span class='glyphicon glyphicon-ok green'></span>";
var playlistfalse = "";

// origin: 0 if newly entered, 1 if from history

function getParentIfSpan(target) {
    if($(target).prop("tagName") == "SPAN") {
        return $(target).parent();
    }
    else {
        return $(target);
    }
}

function TrackmanTimer(button, finish) {
    this.interval = null;
    this.seconds = timerlength;
    this.button = button

    // the finish action is expected to handle the event, e.g. log the track
    this.finish = finish;
}

TrackmanTimer.prototype.start = function() {
    // if it's already ticking, bail out
    if(this.button.data("ticking") == true) {
        return;
    }

    this.button.data("ticking", true);
    this.button.find("span").remove();
    this.button.html(this.seconds);

    var inst = this;
    this.interval = setInterval(function() {
        inst.seconds--;
        if(inst.seconds <= 0) {
            inst.finish();
            inst.clear();
        }
        else {
            inst.button.html(inst.seconds);
        }
    }, 1000);
};

TrackmanTimer.prototype.clear = function() {
    this.seconds = timerlength;
    if(this.interval != undefined) {
        clearInterval(this.interval);
    }

    this.button.data("ticking", false);
    this.button.html(clockspan);
};

function Trackman(baseUrl, djsetId, djId) {
    this.baseUrl = baseUrl;
    this.djsetId = djsetId;
    this.djId = djId;
    this.rotations = {};
    this.timers = {'queue': null, 'search': null};
    this.completeTimer = null;
    this.eventSource = null;
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
    if(track['artist'] == undefined || track['artist'] == "") {
        alert("Must fill out the artist field");
        return false;
    }
    if(track['title'] == undefined || track['title'] == "") {
        alert("Must fill out the title field");
        return false;
    }
    if(track['album'] == undefined || track['album'] == "") {
        alert("Must fill out the album field");
        return false;
    }
    if(track['label'] == undefined || track['label'] == "") {
        alert("Must fill out the label field");
        return false;
    }
    return true;
};

// Autologout {{{
Trackman.prototype.initAutologout = function() {
    this.extendAutologout = false;

    $.ajax({
        url: this.baseUrl + "/api/autologout",
        dataType: "json",
        success: this.updateAutologout,
    });
    $('#id_extend_autologout').on('change', null, {'instance': this},
                                  this.toggleAutologout);
};

Trackman.prototype.toggleAutologout = function(ev) {
    var inst = ev.data.instance;

    $('#id_extend_autologout').prop('disabled', true);

    var formdata = {};

    if($('#id_extend_autologout').prop('checked')) {
        formdata['autologout'] = "disable";
    } else {
        formdata['autologout'] = "enable";
    }

    $.ajax({
        url: inst.baseUrl + "/api/autologout",
        data: formdata,
        dataType: "json",
        type: "POST",
        context: inst,
        success: inst.updateAutologout,
        error: inst.updateAutologoutError,
    });
};

Trackman.prototype.updateAutologout = function(data) {
    $('#id_extend_autologout').prop('disabled', false);

    if(data['success'] == false) {
        alert(data['message']);
    } else if(data['autologout'] == true) {
        this.extendAutologout = false;
    } else {
        this.extendAutologout = true;
    }

    $('#id_extend_autologout').prop('checked', this.extendAutologout);
};

Trackman.prototype.updateAutologoutError = function(jqXHR, textStatus, errorThrown) {
    $('#id_extend_autologout').prop('disabled', false);
    this.handleError(jqXHR, textStatus, errorThrown);
    $('#id_extend_autologout').prop('checked', this.extendAutologout);
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
    this.clearTimer("queue");

    var elem = element;
    var id = element.prop("id").substring(1);
    var track = this.queue[id];
    function postLog(data) {
        if(data['success'] == false) {
            alert(data['message']);
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
    return this.queueFromList(JSON.parse(data));
};

Trackman.prototype.queueFromList = function(tracks) {
    for(i in tracks) {
        var track = tracks[i];
        if(this.validateTrack(track)) {
            track['origin'] = 0;
            this.queue.push(track);
        }
    }

    this.saveQueue();
    this.updateQueue();
};

// }}}

// Playlist {{{
Trackman.prototype.initPlaylist = function() {
    this.pauseComplete = false;
    this.pauseSearch = false;
    this.playlist = [];
    var inst = this;

    var thread = null;
    function entryChanged(target) {
        inst.pauseComplete = false;
        inst.pauseSearch = false;
        inst.delayAutoCompleteField(target.prop('name'));

        clearTimeout(thread);
        thread = setTimeout(function() {
            inst.searchForm();
        }, 350);
    }

    $(".trackman-entry input").on('mouseover', function () {
        inst.pauseComplete = true;
    });
    $(".trackman-entry input").on('blur', function () {
        entryChanged($(this));
    });
    $(".trackman-entry input").on('focus', function () {
        entryChanged($(this));
    });
    $(".trackman-entry input").on('keydown', function (ev) {
        if(ev.key != "ArrowUp" && ev.key != "ArrowDown" && ev.key != "ArrowLeft" && ev.key != "ArrowRight" && ev.key != "Tab" && ev.key != "Escape") {
            entryChanged($(this));
        } else {
            inst.pauseComplete = true;
            inst.pauseSearch = true;
        }
    });
    $("button#new-log").bind('click', {'instance': this}, this.logNewTrack);
    $("button#clear-form").bind('click', {'instance': this}, this.clearForm);
    $(".trackman-search-results").on('click', function () {
        inst.pauseSearch = true;
    });

    this.updatePlaylist();
};

Trackman.prototype.logTrack = function(track, callback) {
    if(this.djsetId != null) {
        $.ajax({
            url: this.baseUrl + "/api/tracklog",
            data: {
                "track_id": track['id'],
                "djset_id": this.djsetId,
                "vinyl":    track['vinyl'],
                "request":  track['request'],
                "new":      track['new'],
                "rotation": track['rotation'],
            },
            context: this,
            type: "POST",
            success: callback,
            error: function(jqXHR, statusText, errorThrown) {
                if(jqXHR.responseJSON['onair'] == false) {
                    this.djsetId = null;
                    this.logTrack(track, callback);
                } else {
                    inst.handleError(jqXHR, statusText, errorThrown);
                }
            },
        });
    } else {
        // create a new DJSet, start using it, and try again
        $.ajax({
            url: this.baseUrl + "/api/djset",
            data: {
                "dj": this.djId,
            },
            context: this,
            type: "POST",
            success: function(data) {
                this.djsetId = data['djset_id'];
                this.logTrack(track, callback);
            },
            error: this.handleError,
        });
    }
};

Trackman.prototype.createTrack = function(track, callback) {
    $.ajax({
        url: this.baseUrl + "/api/track",
        data: {
            "artist": track['artist'],
            "album": track['album'],
            "title": track['title'],
            "label": track['label'],
        },
        type: "POST",
        context: this,
        success: function(data) {
            if(data['success'] == false) {
                alert(data['message']);
                return;
            }
            track['id'] = data['track_id'];
            this.logTrack(track, callback);
        },
        error: this.handleError,
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
            alert(data['message']);
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
            url: this.baseUrl + "/api/tracklog/edit/" + id,
            type: "DELETE",
            dataType: "json",
            context: this,
            success: function(data) {
                if(data['success'] == false) {
                    alert(data['message']);
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
    if(this.djsetId != null) {
        $.ajax({
            url: this.baseUrl + "/api/djset/" + this.djsetId,
            data: {
                "merged": true,
            },
            dataType: "json",
            context: this,
            success: function(data) {
                if(data['success'] == false) {
                    alert(data['message']);
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
    } else {
        this.playlistKeyed = [];
        callback();
    }
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
    if(typeof tableclass == "undefined" || tableclass == "queue") {
        if(this.timers['queue'] != null) {
            this.timers['queue'].clear();
            this.timers['queue'] = null;
        }
    }

    if(typeof tableclass == "undefined" || tableclass == "search") {
        if(this.timers['search'] != null) {
            this.timers['search'].clear();
            this.timers['search'] = null;
        }
    }
};
// }}}

// Search {{{
Trackman.prototype.initSearch = function() {
    this.searchResults = [];
    this.bindSearchListeners();

    this.searchLists = ['artist', 'title', 'album', 'rlabel'];
    for(var i in this.searchLists) {
        var listId = this.searchLists[i] + '_autocomplete';
        var listElem = $('<datalist>');
        listElem.prop('id', listId);
        $('body').append(listElem);
        $('input#' + this.searchLists[i]).attr('list', listId);
        $('input#' + this.searchLists[i]).prop('autocomplete', "off");
    }
};

Trackman.prototype.logSearch = function(element) {
    this.clearTimer("search");

    var elem = element;
    var id = element.prop("id").substring(1);
    var track = this.searchResults[id];
    function post_log(data) {
        if(data['success'] == false) {
            alert(data['message']);
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

    if(this.pauseSearch) {
        return;
    }

    $.ajax({
        url: this.baseUrl + "/api/search",
        data: this.getFormData(),
        dataType: "json",
        success: function(data) {
            if(this.pauseSearch || data['success'] == false) {
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

Trackman.prototype.autoCompleteField = function(name) {
    var inst = this;
    var searchData = this.getFormData();
    var acData = {};

    if(this.pauseComplete) {
        return;
    }

    if(name == 'rlabel') {
        acData['field'] = "label";
        acData['label'] = searchData['label'];
    }
    else {
        acData['field'] = name;
        acData[name] = searchData[name];
    }

    $.ajax({
        url: this.baseUrl + "/api/autocomplete",
        data: acData,
        dataType: "json",
        success: function(data) {
            if(this.pauseComplete || data['success'] == false) {
                return;
            }
            results = data['results'];

            var listElem = $('#' + name + '_autocomplete');
            listElem.empty();

            for(var i = 0; i < results.length; i++) {
                var elem = $('<option>');
                elem.prop('value', results[i]);
                listElem.append(elem);
            }
        },
    });
};

Trackman.prototype.delayAutoCompleteField = function(name) {
    var inst = this;
    if($('#' + name + '_autocomplete').length == 0) {
        this.autoCompleteField(name);
    }
    else {
        clearTimeout(inst.completeTimer);
        inst.completeTimer = setTimeout(function() {
            inst.autoCompleteField(name);
        }, 350);
    }
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
                                               function(ev) {
        var button = getParentIfSpan(ev.target);
        if(button.data('ticking') != true) {
            ev.data.instance.clearTimer('search');
            ev.data.instance.timers['search'] = new TrackmanTimer(button, function() {
                ev.data.instance.logSearch($(ev.target).parents(".search-row"));
            });
            ev.data.instance.timers['search'].start();
        }
        else {
            ev.data.instance.timers['search'].clear();
        }
    });

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
    var newSelect = $('<select>');
    newSelect.addClass('rotation');
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
        logDelayBtn.bind('click', {'instance': this}, function(ev) {
            var button = getParentIfSpan(ev.target);
            if(button.data('ticking') != true) {
                ev.data.instance.clearTimer('queue');
                ev.data.instance.timers['queue'] = new TrackmanTimer(button, function() {
                    ev.data.instance.logQueued($(ev.target).parents(".queue-row"));
                });
                ev.data.instance.timers['queue'].start();
            }
            else {
                ev.data.instance.timers['queue'].clear();
            }
        });
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
                url: inst.baseUrl + "/api/tracklog/edit/" + id,
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
                        alert(data['message']);
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
    var inst = this;

    $('#report_modal').modal();
    $('#report_modal_tbody').empty();

    $.ajax({
        url: this.baseUrl + "/api/track/" + id,
        dataType: "json",
        context: this,
        success: function(data) {
            if(data['success'] == false) {
                alert(data['message']);
                return;
            }

            var tr = $('<tr>');

            var fields = ['artist', 'title', 'album', 'label'];
            for(var i in fields) {
                var td = $('<td>');
                td.text(data['track'][fields[i]]);
                tr.append(td);
            }

            $('#report_modal_tbody').append(tr);
        },
    });

    $('#report_submit_btn').off('click');
    $('#report_submit_btn').on('click', function() {
        $.ajax({
            url: inst.baseUrl + "/api/track/" + id + "/report",
            data: {
                'dj_id': inst.djId,
                'reason': $('#id_report_reason').val(),
            },
            dataType: "json",
            type: "POST",
            context: this,
            success: function(data) {
                if(data['success'] == false) {
                    alert(data['message']);
                    return;
                }

                inst.showAlert("Your report has been submitted. Thanks for helping to improve our track library!");
                $('#id_report_reason').val('');
                $('#report_modal').modal('hide');
            },
        });
    });
};

Trackman.prototype.handleError = function(jqXHR, statusText, errorThrown) {
    if(statusText == "error") {
        try {
            var data = JSON.parse(jqXHR.responseText);
            alert(data['message']);
        } catch(e) {
            alert(statusText);
        }
    } else {
        alert(statusText);
    }
};

Trackman.prototype.showAlert = function(msg) {
    var alertDiv = $('<div>');
    alertDiv.addClass('alert alert-info');
    alertDiv.text(msg);

    var closeBtn = $('<button>');
    closeBtn.addClass('close');
    closeBtn.attr('type', 'button');
    closeBtn.attr('data-dismiss', 'alert');
    closeBtn.html('&times;');
    alertDiv.prepend(closeBtn);

    $('#trackman_alerts').append(alertDiv);
    alertDiv.show('fast');
};

Trackman.prototype.initEventHandler = function() {
    if(typeof EventSource == 'undefined') {
        // cannot use server-sent events, boo
        return;
    }

    this.eventSource = new EventSource(this.baseUrl + '/api/live');
    this.eventSource.trackman = this;
    this.eventSource.onmessage = function(ev) {
        msg = JSON.parse(ev.data);

        switch(msg['event']) {
            case 'message':
                this.trackman.showAlert(msg['data']);
                break;
            case 'session_end':
                this.djsetId = null;
                break;
        }
    };
};

Trackman.prototype.adjustPanelHeights = function() {
    var rowTableHeight = ($(window).height() - $('nav').height() - $('.trackman-entry').height() - 20 * 8) / 3 - $('#trackman_playlist_panel > .table:first-child').height();

    // enforce a minimum height of 50 pixels
    if(rowTableHeight < 50) {
        rowTableHeight = 50;
    }

    $('.row-table').height(rowTableHeight);
};

Trackman.prototype.initResizeHandler = function() {
    var inst = this;
    var resizeTimeout;

    // do an immediate resize
    this.adjustPanelHeights();

    // The MDN documentation indicates that this event handler shouldn't
    // execute computationally expensive operations directly since it can fire
    // at a high rate, so we throttle resize events to 15 fps
    $(window).on('resize', null, {}, function() {
        if(!resizeTimeout) {
            resizeTimeout = setTimeout(function() {
                resizeTimeout = null;
                inst.adjustPanelHeights();
            }, 66);
        }
    });
};

Trackman.prototype.initLogout = function() {
    var inst = this;
    $('#trackman_logout_btn').on('click', {}, function() {
        inst.eventSource.close();
        inst.clearQueue();
        inst.saveQueue();

        if(inst.djsetId != null) {
            $.ajax({
                url: inst.baseUrl + "/api/djset/" + inst.djsetId + "/end",
                data: {
                    'email_playlist': $('#id_email_playlist').prop('checked'),
                },
                dataType: "json",
                type: "POST",
                success: function(data) {
                    if(data['success'] == false) {
                        alert(data['message']);
                    }

                    location.href = inst.baseUrl;
                },
            });
        } else {
            location.href = inst.baseUrl;
        }
    });
};

Trackman.prototype.initRotations = function() {
    var inst = this;
    $.ajax({
        'url': this.baseUrl + "/api/rotations",
        success: function(data) {
            inst.rotations = data['rotations'];
            inst.renderRotation($('#rotation'), 1);
        },
    });
};

Trackman.prototype.init = function() {
    this.initLogout();
    this.initResizeHandler();
    this.initEventHandler();
    this.initAutologout();
    this.initRotations();
    this.initQueue();
    this.initPlaylist();
    this.initSearch();
};

// @license-end
