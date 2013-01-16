import config
import lib
from flask import Flask, Request, redirect, request, url_for
from flask.ext.csrf import csrf
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from urlparse import urlparse, urljoin

app = Flask(__name__)
app.config.from_object(config)
app.request_class = lib.Request
csrf(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.setup_app(app)


def format_datetime(value, format=None):
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")
app.jinja_env.filters['datetime'] = format_datetime

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

import wuvt.views

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('127.0.0.1',
                               app.config['MAIL_FROM'],
                               app.config['ADMINS'], "WUVT website error")
    mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Time:               %(asctime)s

%(message)s
'''))
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
