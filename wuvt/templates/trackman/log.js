var djset_id = {{ djset_id or "null" }};
var dj_id = {{ dj_id }};
// Dictionary mapping rotation_ids to strings
var rotations = {{ rotations|tojson|safe }};

var t = new Trackman(djset_id, dj_id, rotations);
t.init();
