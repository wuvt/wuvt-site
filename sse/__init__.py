import redis


def application(e, start_response):
    headers = []
    headers.append(('Content-Type', 'text/event-stream; charset=utf-8'))
    headers.append(('Cache-Control', 'no-cache'))
    start_response('200 OK', headers)

    yield 'event: ping\n\n'

    redis_conn = redis.from_url(e.get('SSE_SERVER', 'redis://localhost:6379'))
    pubsub = redis_conn.pubsub()
    pubsub.subscribe(e['SSE_CHANNEL'])
    for msg in pubsub.listen():
        if msg['type'] == 'message':
            yield 'data: {0}\n\n'.format(msg['data'])
