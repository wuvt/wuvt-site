from dateutil import tz
from . import defaults
from . import session
from flask import Flask, Request, json
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_seasurf import SeaSurf
from flask_sqlalchemy import SQLAlchemy
from kombu.serialization import register
from werkzeug.contrib.cache import RedisCache
import os
import redis

json_mimetypes = ['application/json']

register('flaskjson', json.dumps, json.loads,
         content_type='application/x-flaskjson',
         content_encoding='utf-8')


def localize_datetime(fromtime):
    return fromtime.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())


def format_datetime(value, format=None):
    value = localize_datetime(value)
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")


def format_currency(value):
    return "${:,.2f}".format(value)


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
app.config.from_pyfile(os.environ.get('APP_CONFIG_PATH', 'config.py'))
app.request_class = JSONRequest
app.jinja_env.filters['datetime'] = format_datetime
app.jinja_env.filters['isodatetime'] = lambda d: d.isoformat() + 'Z'
app.jinja_env.filters['format_currency'] = format_currency
app.static_folder = 'static'

if app.config['PROXY_FIX']:
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app,
                            num_proxies=app.config['PROXY_FIX_NUM_PROXIES'])

redis_conn = redis.from_url(app.config['REDIS_URL'])
app.session_interface = session.RedisSessionInterface(redis_conn)

cache = RedisCache(host=redis_conn)
csrf = SeaSurf(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

from wuvt import admin
app.register_blueprint(admin.bp, url_prefix='/admin')

from wuvt import auth
app.register_blueprint(auth.bp, url_prefix='/auth')

if app.config['DONATE_ENABLE']:
    from wuvt import donate
    app.register_blueprint(donate.bp, url_prefix='/donate')

from wuvt import trackman
app.register_blueprint(trackman.bp)
app.register_blueprint(trackman.private_bp, url_prefix='/trackman')


@app.context_processor
def inject_nowplaying():
    track = trackman.trackinfo()
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


from wuvt import models
from wuvt import views

if not app.debug:
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
