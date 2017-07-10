import click
import os.path
import random
import string
import subprocess
from wuvt import app, db_utils


@app.cli.command()
def init_embedded_db():
    """Initialize and seed the embedded database with sample data."""

    # The SQLALCHEMY_DATABASE_URI config option will match the corresponding
    # environment variable when we are using the embedded database.
    if app.config['SQLALCHEMY_DATABASE_URI'] != \
            os.getenv('SQLALCHEMY_DATABASE_URI'):
        return

    click.echo("Initialize the database...")

    # Generate a random password for the admin user
    password = ''.join(random.SystemRandom().sample(
        string.ascii_letters + string.digits, 12))
    click.echo('Password for admin will be set to: {0}'.format(password))

    db_utils.initdb('admin', password)

    click.echo("Database initialized.")

    click.echo("Add sample data...")
    db_utils.add_sample_data()
    click.echo("Sample data added.")


@app.cli.command()
@click.option('--username', default="admin")
@click.password_option()
def initdb(username, password):
    """Initialize the database."""
    click.echo("Initialize the database...")
    db_utils.initdb(username, password)
    click.echo("Database initialized.")


@app.cli.command()
def sampledata():
    """Add some sample data to the database."""
    click.echo("Add sample data...")
    db_utils.add_sample_data()
    click.echo("Sample data added.")


@app.cli.command()
def render_images():
    """Render the predefined SVGs in static/img into appropriately-sized
    PNGs."""
    imgpath = os.path.join(app.static_folder, 'img')
    sources = [
        ('moon.svg', 1200, 42),
        ('logo.svg', 200, 85),
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
