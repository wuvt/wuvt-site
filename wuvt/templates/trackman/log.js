var csrf_token = "{{ csrf_token() }}";
var djset_id = {{ djset.id }};
var dj_id = {{ djset.dj.id }};
// Dictionary mapping rotation_ids to strings
var rotations = {{ rotations|tojson|safe }};

var t = new Trackman(csrf_token, djset_id, dj_id, rotations);
t.init();
