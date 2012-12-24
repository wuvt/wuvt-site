import flask
import json
import lxml.etree
import requests
import urlparse

json_mimetypes = ['application/json']


class Request(flask.Request):
    # from http://flask.pocoo.org/snippets/45/
    def wants_json(self):
        mimes = json_mimetypes
        mimes.append('text/html')
        best = self.accept_mimetypes.best_match(mimes)
        return best in json_mimetypes and \
            self.accept_mimetypes[best] > \
            self.accept_mimetypes['text/html']


def stream_listeners(url):
    parsed = urlparse.urlparse(url)
    r = requests.get(url, auth=(parsed.username, parsed.password))
    doc = lxml.etree.fromstring(r.text)
    listeners = doc.xpath('//icestats/listeners/text()')[0]
    return int(listeners)
