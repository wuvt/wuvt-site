var djset_id = {{ djset_id or "null" }};
var dj_id = {{ dj_id }};

var t = new Trackman("/trackman", djset_id, dj_id);
t.init();
