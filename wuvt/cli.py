import click
from wuvt import app, db, sample_data
from wuvt.blog.models import Category
from wuvt.trackman.models import DJ, Rotation
from wuvt.models import User


@app.cli.command()
@click.option('--username', default="admin")
@click.password_option()
def initdb(username, password):
    """Initialize the database."""
    click.echo("Initialize the database...")

    db.create_all()

    dj = DJ(u"Automation", u"Automation", False)
    db.session.add(dj)
    db.session.commit()

    cats = [Category(u"Events", u"events", True),
            Category(u"Music Adds", u"music-adds", True),
            Category(u"Programming", u"programming", True),
            Category(u"Updates", u"station-updates", True),
            Category(u"Woove", u"woove", True)]
    for cat in cats:
        db.session.add(cat)

    # Create the first account
    click.echo("Create {0} user...".format(username))
    user = User(unicode(username), unicode(username),
                u"{0}@localhost".format(username))
    user.set_password(unicode(password))
    db.session.add(user)

    # The first Rotation is always the default
    db.session.add(Rotation(u"None"))
    map(db.session.add, map(Rotation, [u"Metal", u"New Music", u"Jazz", u"Rock", u"Americana"]))

    db.session.commit()

    click.echo("Database initialized.")


@app.cli.command()
def sampledata():
    """Add some sample data to the database."""
    click.echo("Add sample data...")

    sample_data.add_sample_articles()
    sample_data.add_sample_pages()
    sample_data.add_sample_djs()
    sample_data.add_sample_tracks()

    click.echo("Sample data added.")
