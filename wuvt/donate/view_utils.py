from flask import json
from wuvt import redis_conn


def load_premiums_config():
    premiums_config = redis_conn.get('donate_premiums_config')
    if premiums_config is not None:
        try:
            data = json.loads(premiums_config)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}

    if 'enabled' not in data:
        data['enabled'] = False

    return data
