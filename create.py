#!/usr/bin/python2

from wuvt import db
from wuvt.trackman.models import DJ

db.drop_all()
db.create_all()

dj = DJ("Automation", "Automation")
db.session.add(dj)
db.session.commit()
