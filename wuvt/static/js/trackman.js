var timerlength = 30;

var clockspan = "<span class='glyphicon glyphicon-time'></span>";
var playlisttrue = "<span class='glyphicon glyphicon-ok green'></span>";
var playlistfalse = "";

var playlistrow = "<tr class='playlist-row' id='p{0}'>" +
"<td class='airtime'>{1}</td>" +
"<td class='artist'>{2}</td>" +
"<td class='title'>{3}</td>" +
"<td class='album'>{4}</td>" +
"<td class='rlabel'>{5}</td>" +
"<td class='request'>{6}</td>" +
"<td class='vinyl'>{7}</td>" +
"<td class='new'>{8}</td>" +
"<td class='rotation'>{9}</td>" +
"<td>" +
"<div class='btn-group playlist-actions' role='group'>" +
"<button class='btn btn-default btn-sm playlist-edit' title='Edit this track'><span class='glyphicon glyphicon-pencil'></span></button>" +
"<button class='btn btn-default btn-sm report' title='Report this track for editing'><span class='glyphicon glyphicon-flag'></span></button>" +
"<button class='btn btn-danger btn-sm playlist-delete' title='Delete this track from playlist'><span class='glyphicon glyphicon-trash'></span></button>" +
"</div>" +
"</td>" +
"</tr>";

var airlogrow = "<tr class='playlist-row airlog-row' id='a{0}'>" + 
"<td class='airtime'>{1}</td>" +
"<td class='logtype'>{2}</td>" + 
"<td class='logid'>{3}</td>" +
"</tr>";


var searchrow = "<tr class='search-row' id='s{0}'>" + 
"<td class='artist'>{1}</td>" + 
"<td class='title'>{2}</td>" + 
"<td class='album'>{3}</td>" + 
"<td class='rlabel'>{4}</td>" + 
"<td class='request'><input type='checkbox' name='request'></td>" + 
"<td class='vinyl'><input type='checkbox' name='vinyl'></td>" + 
"<td class='new'><input type='checkbox' name='new'></td>" +
"<td class='rotation'><select class='rotation'></select></td>" +
"<td><div class='btn-group search-actions'>" +
"<button class='btn btn-default btn-sm search-queue' type='button' title='Add to the queue.'><span class='glyphicon glyphicon-plus blue'></span></button>" +
"<button class='btn btn-default btn-sm search-log' type='button' title='Log this track now.'><span class='glyphicon glyphicon-play'></span></button>" +
"<button class='btn btn-default btn-sm search-delay' type='button' title='Log this track in 30 seconds.'><span class='glyphicon glyphicon-time'></span></button>" +
"<button class='btn btn-default btn-sm report' title='Report this track for editing'><span class='glyphicon glyphicon-flag'></span></button>" +
"</div></td>" +
"</tr>";

var queuerow = "<tr class='queue-row' id='q{0}'>" + 
"<td class='artist'>{1}</td>" + 
"<td class='title'>{2}</td>" + 
"<td class='album'>{3}</td>" + 
"<td class='rlabel'>{4}</td>" + 
"<td class='request'><input type='checkbox' name='request'></td>" + 
"<td class='vinyl'><input type='checkbox' name='vinyl'></td>" + 
"<td class='new'><input type='checkbox' name='new'></td>" +
"<td class='rotation'><select class='rotation'></select></td>" +
"<td><div class='btn-group queue-actions'>" +
"<button class='btn btn-default btn-sm queue-log' type='button' title='Log this track now!'><span class='glyphicon glyphicon-play'></span></button>" +
"<button class='btn btn-default btn-sm queue-delay' type='button' title='Log this track in 30 seconds.'><span class='glyphicon glyphicon-time'></span></button>" +
"<button class='btn btn-danger btn-sm queue-delete' type='button' title='Remove from the queue.'><span class='glyphicon glyphicon-remove'></span></button>" +
"</div></td>" +
"</tr>";

// The data is the same origin indicates 0 if newly entered, 1 if from history
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

    this.bindQueueListeners();
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

    // FIXME: this should not replace the entire existing queue; this will
    // require modifications to bindQueueListeners as well
    $("table#queue tbody tr").remove()
    for (var i = 0; i < this.queue.length; i++) {
        var result = this.queue[i];
        $("table#queue tbody").append(queuerow.format(i, result['artist'], result['title'], result['album'], result['label']));
        var row = $("table#queue tbody tr#q" + i);
        row.find(".request input").prop("checked", result['request']);
        row.find(".vinyl input").prop("checked", result['vinyl']);
        row.find(".new input").prop("checked", result['new']);
        this.renderRotation(row.find("select.rotation"), result['rotation']);
    }

    this.bindQueueListeners();
};

Trackman.prototype.bindQueueListeners = function() {
    // XXX: do we need to clear existing event listeners first?

    // request/new/vinyl checkbox listener
    $("table#queue input[type=checkbox]").bind('change', {'instance': this},
                                               function(ev) {
        ev.data.instance.queue[$(ev.target).parents(".queue-row").prop("id").substring(1)][$(ev.target).prop("name")] = this.checked;
    });

    // rotation listener
    $("table#queue select.rotation").bind('change', {'instance': this},
                                          function(ev) {
        ev.data.instance.queue[$(ev.target).parents(".queue-row").prop("id").substring(1)]['rotation'] = $(ev.target).val();
    });

    $("table#queue button.queue-delay").bind('click', {'instance': this},
                                             this.logTimer);

    $("button.queue-log").bind('click', {'instance': this}, function(ev) {
        ev.data.instance.logQueued($(ev.target).parents(".queue-row"));
    });

    $("table#queue button.queue-delete").bind('click', {'instance': this},
                                              function(ev) {
        ev.data.instance.removeFromQueue($(ev.target).parents(".queue-row"));
    });
};

Trackman.prototype.logQueued = function(element) {
    var elem = element;
    var id = element.prop("id").substring(1);
    var track = this.queue[id]
    function postLog(data) {
        if(data['success'] == false) {
            alert(data['error']);
            return;
        };
        this.queue.splice(id, 1);
        this.updateQueue();
        this.updatePlaylist();
    };

    // Delete it from the queue if it's there
    if (track['origin'] == 1) {
        this.logTrack(track, postLog);
    }
    else if (track['origin'] == 0) {
        this.createTrack(track, postLog);
    }

    this.saveQueue();
};

Trackman.prototype.addToQueue = function(element) {
    var id = $(element).prop("id").substring(1);
    var queue_entry = $.extend(true, {}, this.searchResults[id]);
    this.queue.push(queue_entry);
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
};

Trackman.prototype.queueFromJson = function(data) {
    // TODO

    this.saveQueue();
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

    this.bindPlaylistListeners();
    this.updatePlaylist();
};

Trackman.prototype.logTrack = function(track, callback) {
    $.ajax({
        url: "/trackman/api/tracklog",
        data: { "track_id": track['id'],
                "djset_id": djset_id,
                "vinyl":    track['vinyl'],
                "request":  track['request'],
                "new":      track['new'],
                "rotation": track['rotation']
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
                this.updatePlaylist();
            },
        });
    }
    else {
        // This is an airlog
    }
};

Trackman.prototype.editTrack = function() {
    function completeEdit(data) {
        if (data['success'] == false) {
            alert(data['error']);
            return;
        }
        opener.update_playlist();
        window.close();
    }

    var track = this.getFormData();
    if(!this.validateTrack(track)) {
        return false;
    }
    $.ajax({
        url: "/trackman/api/tracklog/edit/" + tracklog_id,
        data: { "artist":   track['artist'],
                "album":    track['album'],
                "title":    track['title'],
                "label":    track['label'],
                "vinyl":    track['vinyl'],
                "request":  track['request'],
                "new":      track['new'],
                "rotation": track['rotation']
        },
        dataType: "json",
        type: "POST",
        success: completeEdit,
    });
};

Trackman.prototype.updatePlaylist = function() {
    var inst = this;
    $.ajax({
        url: "/trackman/api/djset/" + djset_id,
        data: {
            "merged": true,
        },
        dataType: "json",
        success: function(data) {
            if (data['success'] == false) {
                alert(data['error']);
                return;
            }
            playlist = data['logs'];
            inst.renderPlaylist();
        },
    });
};

Trackman.prototype.renderRotation = function(selement, id) {
    for(r in this.rotations) {
        var opt = document.createElement('option');
        $(opt).attr('value', r);
        $(opt).text(this.rotations[r]);
        $(selement).append(opt);
    }

    if(typeof id != "undefined") {
        $(selement).val(id);
    }
};

Trackman.prototype.renderPlaylist = function() {
    // Empty the old playlist
    $("table#playlist tbody tr").remove();
    for (var i = 0; i < playlist.length; i++) {
        var p = playlist[i];
        // If logid is defined it's an airlog
        if ('logid' in p) {
        }
        else {
            // Generate a date string
            var played = new Date(p['played']);
            function pad(value) {
                return ("00" + value).slice(-2);
            }
            played = "{0}:{1}:{2}".format(pad(played.getHours()), pad(played.getMinutes()), pad(played.getSeconds()));
            // Generate the rotation string
            var rotation = rotations[p['rotation_id']];
            if (typeof rotation == "undefined") {
                rotation = rotations[1];
            }
            var request = p['request'] ? playlisttrue : playlistfalse;
            var vinyl = p['vinyl'] ? playlisttrue : playlistfalse;
            var new_track = p['new'] ? playlisttrue : playlistfalse;
            var row = playlistrow.format(p['tracklog_id'], played,
                    p['track']['artist'], p['track']['title'],
                    p['track']['album'], p['track']['label'], request, vinyl,
                    new_track, rotation);
            $("table#playlist tbody").append(row);
        }
    }
    if (playlist.length > 0) {
        this.bindPlaylistListeners();
        // Scroll to bottom
        var pos = $("table#playlist tbody tr:last").position();
        var scrollwindow = $("table#playlist").parent();
        scrollwindow.scrollTop(scrollwindow.scrollTop() + pos.top);
    }
};

Trackman.prototype.clearTimer = function(tableclass) {
    if (typeof tableclass != "undefined") {
        if (typeof delaybutton != "undefined") {
            if (delaybutton.parents("table").prop("id") == tableclass) {
                delaybutton.html(clockspan);
                delaybutton.off("click");
                delaybutton.bind('click', {'instance': this}, this.logTimer);
                clearInterval(delayinterval);
            }
        }
    }
    else {
        if (typeof delayinterval != "undefined") {
            clearInterval(delayinterval);
        }
        if (typeof delaybutton != "undefined") {
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
            if (button.parents("table").prop("id") == "queue") {
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

Trackman.prototype.bindPlaylistListeners = function() {
    $("button.playlist-delete").bind('click', {'instance': this},
                                     function(ev) {
        ev.data.instance.deleteTrack($(ev.target).parents(".playlist-row"));
    });

    // TODO: inline editing
    $("table#playlist button.playlist-edit").bind('click', {'instance': this},
                                                  this.openEditWindow);

    $("table#playlist button.report").bind('click', {'instance': this},
                                           function(ev) {
        playlist_id = $(ev.target).parents("tr").prop("id").slice(1);
        tracklog = $.grep(playlist, function(e){ return e.tracklog_id == playlist_id;})[0];
        id = tracklog['track_id'];
        ev.data.instance.reportTrack(id);
    });
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
    if (typeof track['rotation'] != "undefined") {
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
        $("table#search tbody").append(searchrow.format(i, result['artist'], result['title'], result['album'], result['label']));
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
        ev.data.instance.searchResults[$(ev.target).parents(".search-row").prop("id").substring(1)][$(event.target).prop("name")] = this.checked;
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
        id = this.searchResults[search_id]['id']
        ev.data.instance.reportTrack(id);
    });
};
// }}}

Trackman.prototype.openEditWindow = function(ev) {
    var inst = ev.data.instance;
    var url;
    var id = $(ev.target).parents(".playlist-row").prop("id");
    if (id.substring(0,1) == "p") {
        url = "/trackman/edit/" + id.slice(1);
    }
    else {
        // TODO Set edit url for airlog
    }
    var edit_win = window.open(url, "editWindow", "height=600,width=1200");
    edit_win = update_parent = inst.updatePlaylist();
}

Trackman.prototype.reportTrack = function(id) {
    url = "/trackman/report/" + dj_id + "/" + id;
    var report_win = window.open(url, "reportWindow", "height=600,width=1200");
}

Trackman.prototype.init = function() {
    $('#trackman_logout_btn').click(function() {
        var email = ($('#id_email_playlist:checked').val() == "on") ? 'true' : 'false';
        $("#trackman_logout_form input[name='email_playlist']").val(email);

        $('#trackman_logout_form').submit();
    });

    this.initAutologout();
    this.initQueue();
    this.initPlaylist();
    this.initSearch();
};
