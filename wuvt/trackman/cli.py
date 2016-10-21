from .. import app
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
