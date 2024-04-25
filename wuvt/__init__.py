import dateutil.parser
from dateutil import tz
from flask import Flask, Request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_caching.backends import RedisCache
import json
import humanize
import os
import redis
from . import defaults
import uuid
import datetime
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

try:
    import uwsgi
except ImportError:
    pass

json_mimetypes = ['application/json']


def localize_datetime(fromtime):
    return fromtime.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())


def format_datetime(value, format=None):
    # convert str as needed to deal with API responses
    if type(value) == str:
        value = dateutil.parser.parse(value)

    value = localize_datetime(value)
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")


def format_isodatetime(value):
    # convert str as needed to deal with API responses
    if type(value) == str:
        value = dateutil.parser.parse(value)

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
    app.config.from_file(config_path, load=json.load, silent=True)

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
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app,
                            x_for=app.config['PROXY_FIX_NUM_PROXIES'],
                            x_proto=app.config['PROXY_FIX_NUM_PROXIES'],
                            x_host=app.config['PROXY_FIX_NUM_PROXIES'],
                            x_prefix=app.config['PROXY_FIX_NUM_PROXIES'])

redis_conn = redis.from_url(app.config['REDIS_URL'])

cache = RedisCache(host=redis_conn)
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from wuvt.auth import AuthManager, current_user
auth_manager = AuthManager()
auth_manager.db = db
auth_manager.init_app(app)

if len(app.config['SENTRY_DSN']) > 0:
    sentry_sdk.init(
        app.config['SENTRY_DSN'],
        integrations=[
            FlaskIntegration(),
            RedisIntegration(),
            SqlalchemyIntegration(),
        ])


@app.context_processor
def inject_nowplaying():
    return {
        'current_track': "Not Available",
        'current_dj': "Not Available",
        'current_dj_id': 0,
    }
#    from wuvt.playlists import trackinfo
#    try:
#        track = trackinfo()
#    except IOError:
#        track = None
#
#    if not track:
#        return {
#            'current_track': "Not Available",
#            'current_dj': "Not Available",
#            'current_dj_id': 0,
#        }
#
#    return {
#        'current_track': "{artist} - {title}".format(**track),
#        'current_dj': track['dj'],
#        'current_dj_id': track['dj_id']
#    }


@app.context_processor
def inject_categories():
    from wuvt.blog import list_categories_cached
    return {'categories': list_categories_cached()}


@app.context_processor
def inject_year():
    return {'year': datetime.date.today().strftime("%Y")}


@app.context_processor
def inject_radiothon():
    return {'radiothon': redis_conn.get('radiothon') == b"true"}


@app.after_request
def add_csp(response):
    trackman_public_url = app.config.get('TRACKMAN_PUBLIC_URL',
                                         app.config['TRACKMAN_URL'])
    response.headers['Content-Security-Policy'] = "default-src 'self' https:; script-src 'self' 'unsafe-eval' 'unsafe-inline' https://checkout.stripe.com; style-src 'self' 'unsafe-inline' https://checkout.stripe.com; media-src 'self' *; frame-ancestors 'self'; connect-src 'self' {0}".format(trackman_public_url)
    return response


@app.after_request
def add_app_user_logvar(response):
    if uwsgi is not None and current_user.is_authenticated:
        uwsgi.set_logvar('app_user', current_user.username)
    return response


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

    from wuvt import blog
    app.register_blueprint(blog.bp)

    if app.config['DONATE_ENABLE']:
        from wuvt import donate
        app.register_blueprint(donate.bp, url_prefix='/donate')

    from wuvt import playlists
    app.register_blueprint(playlists.bp)

    from wuvt import cli
    from wuvt import models
    from wuvt import views


init_app()
