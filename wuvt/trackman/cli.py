import click
from flask import json
from .. import app, redis_conn
from . import lib


@app.cli.group()
def trackman():
    """Perform operations on the track library and playlist database."""
    pass


@trackman.command()
def deduplicate_all_tracks():
    lib.deduplicate_all_tracks()


@trackman.command()
def email_weekly_charts():
    lib.email_weekly_charts()


@trackman.command()
def prune_empty_djsets():
    lib.prune_empty_djsets()


@trackman.command()
@click.option('--message', prompt=True)
def send_message(message):
    r = redis_conn.publish('trackman_dj_live', json.dumps({
        'event': "message",
        'data': message,
    }))
    click.echo("Message delivered to {0} clients".format(r))
