String.prototype.format = function() {
    var s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};

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
"<div class='btn-group' role='group'>" +
"<button class='btn btn-default btn-sm'><span class='glyphicon glyphicon-pencil'></span></button>" +
"<button class='btn btn-danger btn-sm'><span class='glyphicon glyphicon-trash'></span></button>" +
"</div>" +
"</td>" +
"</tr>"

var airlogrow = "<tr class='playlist-row airlog-row' id='a{0}'>" + 
"<td class='airtime'>{1}</td>" +
"<td class='logtype'>{2}</td>" + 
"<td class='logid'>{3}</td>" +
"</tr>"


var searchrow = "<tr class='search-row' id='s{0}'>" + 
"<td class='artist'>{1}</td>" + 
"<td class='title'>{2}</td>" + 
"<td class='album'>{3}</td>" + 
"<td class='rlabel'>{4}</td>" + 
"<td class='request'><input type='checkbox' name='request'></td>" + 
"<td class='vinyl'><input type='checkbox' name='vinyl'></td>" + 
"<td class='new'><input type='checkbox' name='new'></td>" +
"<td class='rotation'><select class='rotation'></select></td>" +
"<td><div class='btn-group'>" +
"<button class='btn btn-default btn-sm search-queue' type='button' title='Add to the queue.'><span class='glyphicon glyphicon-plus blue'></span></button>" +
"<button class='btn btn-default btn-sm search-log' type='button' title='Log this track now.'><span class='glyphicon glyphicon-play'></span></button>" +
"<button class='btn btn-default btn-sm search-delay' type='button' title='Log this track in 30 seconds.'><span class='glyphicon glyphicon-time'></span></button>" +
"</div></td>" +
"</tr>"

var queuerow = "<tr class='queue-row' id='q{0}'>" + 
"<td class='artist'>{1}</td>" + 
"<td class='title'>{2}</td>" + 
"<td class='album'>{3}</td>" + 
"<td class='rlabel'>{4}</td>" + 
"<td class='request'><input type='checkbox' name='request'></td>" + 
"<td class='vinyl'><input type='checkbox' name='vinyl'></td>" + 
"<td class='new'><input type='checkbox' name='new'></td>" +
"<td class='rotation'><select class='rotation'></select></td>" +
"<td><div class='btn-group'>" +
"<button class='btn btn-default btn-sm queue-log' type='button' title='Log this track now!'><span class='glyphicon glyphicon-play'></span></button>" +
"<button class='btn btn-default btn-sm queue-delay' type='button' title='Log this track in 30 seconds.'><span class='glyphicon glyphicon-time'></span></button>" +
"<button class='btn btn-danger btn-sm queue-delete' type='button' title='Remove from the queue.'><span class='glyphicon glyphicon-remove'></span></button>" +
"</div></td>" +
"</tr>"

// The data is the same origin indicates 0 if newly entered, 1 if from history
var search_results = [];
var queue = [];
var playlist = [];

function log_search(element) {
    var elem = element;
    var id = element.prop("id").substring(1);
    var track = search_results[id];
    function post_log(data) {
        if (data['success'] == false) {
            alert(data['error']);
        }
        update_playlist();
    };
    log_track(track, post_log);
}

function log_track(track, callback) {
    $.ajax({
        url: "/trackman/api/tracklog",
        data: { "track_id": track['id'],
                "djset_id": djset_id,
                "vinyl":    track['vinyl'],
                "request":  track['request'],
                "new":      track['new'],
                "rotation": track['rotation']
        },
        type: "POST",
        success: callback,
    });
}


function log_queue(element) {
    var elem = element;
    var id = element.prop("id").substring(1);
    var track = queue[id]
    function post_log(data) {
        if (data['success'] == false) {
            alert(data['error']);
        };
        queue.splice(id, 1);
        update_queue();
        update_playlist();
    };

    // Delete it from the queue if it's there
    if (track['origin'] == 1) {
        log_track(track, post_log);
    }
    else if (track['origin'] == 0) {
        create_track(track, post_log);
    }
}

function create_track(track, callback) {
    $.ajax({
        url: "/trackman/api/track",
        data: { "artist": track['artist'],
                "album": track['album'],
                "title": track['title'],
                "label": track['label'],
        },
        type: "POST",
        success: function(data) {
            if (data['success'] == false) {
                alert(data['error']);
            }
            track['id'] = data['track_id'];
            log_track(track, callback);
        },
    });
}

function remove_from_queue(element) {
    id = $(element).prop("id").substring(1);
    queue.splice(id, 1);
    update_queue();
}

function add_to_queue(element) {
    //var track = row_to_object(element);
    /*$("table#search tbody tr#" + id).remove();*/
    var id = $(element).prop("id").substring(1);
    var queue_entry = $.extend(true, {}, search_results[id]);
    queue.push(queue_entry);
    //search_results.splice(id, 1);
    update_history();
    update_queue();
}

function queue_new_track() {
    var track = get_form_data();
    track['origin'] = 0;
    queue.push(track);
    update_queue();
    clear_form();
}

function log_new_track() {
    var track = get_form_data();
    track['origin'] = 0;
    function post_log(data) {
        if (data['success'] == false) {
            alert(data['error']);
        }
        clear_form();
        update_playlist();
    }
    create_track(track, post_log);
}
function clear_form() {
    $(".trackman-entry input").val("");
    $(".trackman-entry input[type=checkbox]").prop("checked", false);
    search_results = [];
    update_history();
}
function get_form_data () {
    return {"artist": $(".trackman-entry input#artist").val(),
            "title": $(".trackman-entry input#title").val(),
            "album": $(".trackman-entry input#album").val(),
            "label": $(".trackman-entry input#rlabel").val(),
            "request": $(".trackman-entry input[name=request]").prop("checked"),
            "vinyl": $(".trackman-entry input[name=vinyl]").prop("checked"),
            "new": $(".trackman-entry input[name=new]").prop("checked"),
            // Will need rotation here TODO
    };

}
function update_queue() {
    $("table#queue tbody tr").remove()
    for (var i = 0; i < queue.length; i++) {
        var result = queue[i];
        $("table#queue tbody").append(queuerow.format(i, result['artist'], result['title'], result['album'], result['label']));
        var row = $("table#queue tbody tr#q" + i);
        row.find(".request input").prop("checked", result['request']);
        row.find(".vinyl input").prop("checked", result['vinyl']);
        row.find(".new input").prop("checked", result['new']);
        render_rotation(row.find("select.rotation"), result['rotation']);
    }
    queue_listeners();
}
function search_history() {
    $.ajax({
        url: "/trackman/api/search",
        data: get_form_data(),
        dataType: "json",
        success: process_history,
    })
}
function process_history(data, status, jqXHR) {
    if (data['success'] == false) return false;
    results = data['results'];
    search_results = [];
    for (var i = 0; i < results.length; i++) {
        results[i]['origin'] = 1;
        search_results.push(results[i])
    }
    update_history();
}
function update_history() {
    // Remove old history results
    $("table#search tbody tr").remove();
    // Add new results
    for (var i = 0; i < search_results.length; i++) {
        var result = search_results[i];
        $("table#search tbody").append(searchrow.format(i, result['artist'], result['title'], result['album'], result['label']));
        var row = $("table#search tbody tr#s" + i);
        row.find(".request input").prop("checked", result['request']);
        row.find(".vinyl input").prop("checked", result['vinyl']);
        row.find(".new input").prop("checked", result['new']);
        render_rotation(row.find("select.rotation"), result['rotation']);

    }
    search_listeners();
}

// Generates the select content, if an id is provided it chooses the option
function render_rotation(selement, id) {
    console.log(selement);
    $(selement).append(rotationoptions);
    if (typeof id != "undefined") {
        $(selement).val(id);
    }
}

function update_playlist() {
    $.ajax({
        url: "/trackman/api/djset/" + djset_id,
        data: {
            "merged": true,
        },
        dataType: "json",
        success: function(data) {
            if (data['success'] == false) {
                alert(data['error']);
            }
            playlist = data['logs'];
            render_playlist();
        },
    })
}

function render_playlist() {
    $("table#playlist tbody tr").remove();
    for (var i = 0; i < playlist.length; i++) {
        var p = playlist[i];
        // If logid is defined it's an airlog
        if ('logid' in p) {
        }
        else {
            // Generate a date string
            var played = new Date(p['played']);
            console.log(played);
            played = "{0}:{1}:{2}".format(played.getHours(), played.getMinutes(), played.getSeconds());
            // Generate the rotation string
            var rotation = rotations[p['rotation_id']];
            if (typeof rotation == "undefined") {
                rotation = rotations[1];
            }
            var row = playlistrow.format(p['tracklog_id'], played,
                    p['track']['artist'], p['track']['title'],
                    p['track']['album'], p['track']['label'], p['request'],
                    p['vinyl'], p['new'], rotation);
            $("table#playlist tbody").append(row);
        }
    }
    //$("table#playlist").
}

function update_search_results(event) {
    search_results[$(event.target).parents(".search-row").prop("id").substring(1)][$(event.target).prop("name")] = this.checked;
}
function update_search_rotation(event) {
    search_results[$(event.target).parents(".search-row").prop("id").substring(1)]['rotation'] = $(event.target).val();
}
function update_queue_data(event) {
    queue[$(event.target).parents(".queue-row").prop("id").substring(1)][$(event.target).prop("name")] = this.checked;
}
function update_queue_rotation(event) {
    queue[$(event.target).parents(".queue-row").prop("id").substring(1)]['rotation'] = $(event.target).val();
}

// Event listener code
function search_listeners() {
    $("button.search-queue").click(function (event) { 
        add_to_queue($(event.target).parents(".search-row"));
    })
    $("button.search-log").click(function (event) { 
        log_search($(event.target).parents(".search-row"));
    })
    $("table#search input[type=checkbox]").change(update_search_results);
    $("table#search select.rotation").change(update_search_rotation);
}

function queue_listeners() {
    $("table#queue input[type=checkbox]").change(update_queue_data);
    $("table#queue select.rotation").change(update_queue_rotation);
    $("button.queue-log").click(function (event) { 
        log_queue($(event.target).parents(".queue-row"));
    });
    $("table#queue button.queue-delete").click(function (event) {
        remove_from_queue($(event.target).parents(".queue-row"));
    });
}

function search_form() {
    $(".trackman-entry input.form-control").each(
            function(index) {
                if ($(this).val().length >= 3) {
                    search_history();
                    return false;
                }
            });
}


// Test code to be removed
$( document ).ready(function() {
    var thread = null;
    $(".trackman-entry input").keyup(function () {
        clearTimeout(thread);
        var target = $(this);
        thread = setTimeout(function() {search_form();}, 350);

    });
    $("button#new-queue").click(queue_new_track);
    $("button#new-log").click(log_new_track);
    update_playlist();
})
