import click
import os
import random
import string
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
