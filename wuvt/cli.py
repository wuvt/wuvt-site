import click
import os.path
import subprocess
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


@app.cli.command()
def render_images():
    """Render the predefined SVGs in static/img into appropriately-sized
    PNGs."""
    imgpath = os.path.join(app.static_folder, 'img')
    sources = [
        ('moon.svg', 1200, 42),
        ('logo.svg', 200, 72),
        ('bubble.svg', 558, 99),
        ('nowplaying_banner_left.svg', 32, 15),
        ('nowplaying_banner_right.svg', 52, 34),
        ('robot.svg', 160, 148),
    ]

    for source in sources:
        for zoom in (1, 2):
            outname = source[0].replace('.svg', '-{0:d}x.png'.format(zoom))
            subprocess.check_call([
                    'rsvg-convert',
                    '-w', str(source[1] * zoom),
                    '-h', str(source[2] * zoom),
                    '-o', os.path.join(imgpath, outname),
                    os.path.join(imgpath, source[0]),
                ])
            subprocess.check_call([
                    'optipng', '-quiet', '-nb', '-nc', '-np',
                    os.path.join(imgpath, outname),
                ])
