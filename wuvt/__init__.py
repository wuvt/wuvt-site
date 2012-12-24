import config
import lib
from flask import Flask, Request
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(config)
app.request_class = lib.Request

db = SQLAlchemy(app)

def format_datetime(value, format=None):
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")
app.jinja_env.filters['datetime'] = format_datetime

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
