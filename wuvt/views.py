from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
from flask.ext.csrf import csrf

from wuvt import app
from wuvt import lib

from wuvt.trackman.views import *


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/live')
def livestream():
    response = Response(sse.event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = "no-cache"
    response.headers['Connection'] = "keep-alive"
    response.headers['X-Accel-Buffering'] = "no"
    return response
