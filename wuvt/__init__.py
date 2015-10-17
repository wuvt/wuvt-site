from dateutil import tz
from wuvt import config
from wuvt import session
from flask import Flask, Request, redirect, request, url_for
from flask.ext.login import LoginManager
from flask.ext.seasurf import SeaSurf
from flask.ext.sqlalchemy import SQLAlchemy
import re
import redis
import unidecode
import urlparse


json_mimetypes = ['application/json']
_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
_slug_pattern = re.compile(r"[^ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._~:/?#\[\]@!$&'()*+,;=\-]*")


def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug and validates that it is an acceptable
    character set as per rfc3986"""
    if _slug_pattern.match(text) == None:
        return False

    # from http://flask.pocoo.org/snippets/5/
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode.unidecode(word).split())
    return unicode(delim.join(result))


def localize_datetime(fromtime):
    return fromtime.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal())


def format_datetime(value, format=None):
    value = localize_datetime(value)
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")


def is_safe_url(target):
    ref_url = urlparse.urlparse(request.host_url)
    test_url = urlparse.urlparse(urlparse.urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def redirect_back(endpoint, **values):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


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
app.config.from_object(config)
app.request_class = JSONRequest
app.jinja_env.filters['datetime'] = format_datetime
app.jinja_env.filters['isodatetime'] = lambda d: d.isoformat() + 'Z'
app.static_folder = 'static'

redis_conn = redis.from_url(app.config['REDIS_URL'])
app.session_interface = session.RedisSessionInterface(redis_conn)

csrf = SeaSurf(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

from wuvt import admin
app.register_blueprint(admin.bp, url_prefix='/admin')

from wuvt import auth
app.register_blueprint(auth.bp, url_prefix='/auth')

from wuvt import donate
app.register_blueprint(donate.bp, url_prefix='/donate-online')

from wuvt import trackman
app.register_blueprint(trackman.bp, url_prefix='/trackman')

from wuvt import views

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler

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
