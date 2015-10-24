#!/usr/bin/python2

from flask.ext.migrate import MigrateCommand
from flask.ext.script import Manager
from wuvt import app, migrate

manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
