#!/usr/bin/env python2

from wuvt import app
from gevent.wsgi import WSGIServer

if __name__ == '__main__':
    app.debug = True
    server = WSGIServer(("", 8080), app)
    server.serve_forever()
