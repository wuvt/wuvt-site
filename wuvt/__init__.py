from dateutil import tz
from flask import Flask, Request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.contrib.cache import RedisCache
import humanize
import os
import redis
import defaults
import uuid

json_mimetypes = ['application/json']


def localize_datetime(fromtime):
    return fromtime.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())


def format_datetime(value, format=None):
    value = localize_datetime(value)
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")


def format_isodatetime(value):
    if value.utcoffset() is None:
        value = value.replace(tzinfo=tz.tzutc())

    return value.isoformat()


def format_currency(value):
    return "${:,.2f}".format(value)


def format_uuid(value):
    try:
        return uuid.UUID(value)
    except:
        return None


class JSONRequest(Request):
    # from http://flask.pocoo.org/snippets/45/
    def wants_json(self):
        mimes = json_mimetypes
        mimes.append('text/html')
        best = self.accept_mimetypes.best_match(mimes)
        return best in json_mimetypes and \
            self.accept_mimetypes[best] > \
            self.accept_mimetypes['text/html']


app = Flask(__name__)
app.config.from_object(defaults)

# use the value of the SQLALCHEMY_DATABASE_URI environment variable as the
# default; any value specified in the config will override this
app.config.setdefault('SQLALCHEMY_DATABASE_URI',
                      os.getenv('SQLALCHEMY_DATABASE_URI'))

config_path = os.environ.get('APP_CONFIG_PATH', 'config.py')
if config_path.endswith('.py'):
    app.config.from_pyfile(config_path, silent=True)
else:
    app.config.from_json(config_path, silent=True)

app.request_class = JSONRequest
app.jinja_env.filters.update({
    'intcomma': humanize.intcomma,
    'intword': humanize.intword,
    'naturalday': humanize.naturalday,
    'naturaldate': humanize.naturaldate,
    'naturaltime': humanize.naturaltime,
    'naturalsize': humanize.naturalsize,

    'datetime': format_datetime,
    'isodatetime': format_isodatetime,
    'format_currency': format_currency,
    'uuid': format_uuid,
})
app.static_folder = 'static'

if app.config['PROXY_FIX']:
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app,
                            num_proxies=app.config['PROXY_FIX_NUM_PROXIES'])

redis_conn = redis.from_url(app.config['REDIS_URL'])

cache = RedisCache(host=redis_conn)
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from wuvt.auth import AuthManager
auth_manager = AuthManager()
auth_manager.db = db
auth_manager.init_app(app)


@app.context_processor
def inject_nowplaying():
    from wuvt.trackman import trackinfo
    track = trackinfo()
    if not track:
        return {
            'current_track': u"Not Available",
            'current_dj': u"Not Available",
            'current_dj_id': 0,
        }

    return {
        'current_track': u"{artist} - {title}".format(**track),
        'current_dj': track['dj'],
        'current_dj_id': track['dj_id']
    }


@app.context_processor
def inject_categories():
    from wuvt.blog import list_categories_cached
    return {'categories': list_categories_cached()}


@app.context_processor
def inject_radiothon():
    return {'radiothon': redis_conn.get('radiothon') == "true"}


if app.debug:
    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
else:
    import logging
    from logging.handlers import SMTPHandler, SysLogHandler

    mail_handler = SMTPHandler(
        app.config['SMTP_SERVER'],
        app.config['MAIL_FROM'],
        app.config['ADMINS'],
        "[{}] Website error".format(app.config['STATION_NAME']))
    mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Time:               %(asctime)s

%(message)s
'''))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

    if 'SYSLOG_ADDRESS' in app.config:
        syslog_handler = SysLogHandler(address=app.config['SYSLOG_ADDRESS'])
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


def init_app():
    from wuvt import admin
    app.register_blueprint(admin.bp, url_prefix='/admin')

    app.register_blueprint(auth_manager.bp, url_prefix='/auth')

    from wuvt import blog
    app.register_blueprint(blog.bp)

    if app.config['DONATE_ENABLE']:
        from wuvt import donate
        app.register_blueprint(donate.bp, url_prefix='/donate')

    from wuvt import trackman
    app.register_blueprint(trackman.bp)
    app.register_blueprint(trackman.private_bp, url_prefix='/trackman')
    app.register_blueprint(trackman.api_bp, url_prefix='/trackman/api')
    app.register_blueprint(trackman.library_bp, url_prefix='/trackman/library')
    # TODO: redirect /admin/library to /trackman/library
    trackman.playlists_cache.init_app(app, config={
        'CACHE_TYPE': "redis",
        'CACHE_REDIS_URL': app.config['REDIS_URL'],
    })
    trackman.charts_cache.init_app(app, config={
        'CACHE_TYPE': "redis",
        'CACHE_REDIS_URL': app.config['REDIS_URL'],
    })

    from wuvt import cli
    from wuvt import models
    from wuvt import views


init_app()
