import gevent
import gevent.monkey
import redis
from wuvt import config

gevent.monkey.patch_all()
red = redis.StrictRedis()


def event_stream():
    pubsub = red.pubsub()
    pubsub.subscribe(config.REDIS_CHANNEL)
    for msg in pubsub.listen():
        if msg['type'] == 'message':
            yield 'data: {0}\n\n'.format(msg['data'])


def send(msg):
    red.publish(config.REDIS_CHANNEL, msg)
