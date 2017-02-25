import uuid
from datetime import timedelta
from redis import Redis
from werkzeug.datastructures import CallbackDict
from flask.sessions import SecureCookieSessionInterface, SessionMixin
from flask.helpers import total_seconds
from itsdangerous import BadSignature


class RedisSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SecureCookieSessionInterface):
    session_class = RedisSession

    def __init__(self, redis=None, prefix='session:'):
        if redis is None:
            redis = Redis()
        self.redis = redis
        self.prefix = prefix

    def generate_sid(self):
        return uuid.uuid4()

    def get_redis_expiration_time(self, app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        s = self.get_signing_serializer(app)
        if s is None:
            return None

        cookie_val = request.cookies.get(app.session_cookie_name)
        if cookie_val:
            max_age = total_seconds(app.permanent_session_lifetime)
            try:
                sid = s.loads(cookie_val, max_age=max_age)
                val = self.redis.get(self.prefix + str(sid))
                if val is not None:
                    data = self.serializer.loads(val)
                    return self.session_class(data, sid=sid)
                else:
                    sid = self.generate_sid()
            except BadSignature:
                sid = self.generate_sid()
        else:
            sid = self.generate_sid()

        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)

        if not session:
            self.redis.delete(self.prefix + str(session.sid))
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain, path=path)
            return

        if not self.should_set_cookie(app, session):
            return

        redis_exp = self.get_redis_expiration_time(app, session)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        expires = self.get_expiration_time(app, session)
        val = self.serializer.dumps(dict(session))
        cookie_val = self.get_signing_serializer(app).dumps(session.sid)

        self.redis.setex(self.prefix + str(session.sid), val,
                         int(total_seconds(redis_exp)))
        response.set_cookie(app.session_cookie_name, cookie_val,
                            expires=expires, httponly=httponly,
                            domain=domain, path=path, secure=secure)
