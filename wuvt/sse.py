import gevent
import gevent.monkey
from wuvt import app
from wuvt import redis_conn

def event_stream():
    pubsub = redis_conn.pubsub()
    pubsub.subscribe(app.config['REDIS_CHANNEL'])
    for msg in pubsub.listen():
        if msg['type'] == 'message':
            yield 'data: {0}\n\n'.format(msg['data'])


def send(msg):
    redis_conn.publish(app.config['REDIS_CHANNEL'], msg)
