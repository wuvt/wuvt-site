from wuvt import config
from wuvt import lib
from wuvt import session
from flask import Flask, Request, redirect, request, url_for
try:
    from flask.ext.csrf import csrf
    from flask.ext.login import LoginManager
    from flask.ext.sqlalchemy import SQLAlchemy
except:
    from flaskext.csrf import csrf
    from flaskext.login import LoginManager
    from flaskext.sqlalchemy import SQLAlchemy
from urlparse import urlparse, urljoin


def format_datetime(value, format=None):
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def redirect_back(endpoint, **values):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


app = Flask(__name__)
app.config.from_object(config)
app.request_class = lib.Request
app.session_interface = session.RedisSessionInterface()
app.jinja_env.filters['datetime'] = format_datetime
csrf(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = "admin.login"
login_manager.init_app(app)

from wuvt import admin
app.register_blueprint(admin.bp, url_prefix='/admin')

from wuvt import trackman
app.register_blueprint(trackman.bp, url_prefix='/trackman')

from wuvt import views

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler(app.config['SMTP_SERVER'],
                               app.config['MAIL_FROM'],
                               app.config['ADMINS'], "[WUVT] Website error")
    mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Time:               %(asctime)s

%(message)s
'''))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
