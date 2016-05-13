#!/usr/bin/env python2

from wuvt import db
from wuvt.blog.models import Category
from wuvt.trackman.models import DJ, Rotation
from wuvt.models import User

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

# There must be a user called 'admin'. This is hardcoded in everything to be the superuser.
user = User(u"admin", u"admin", u"admin@wuvt.vt.edu")
user.set_password(u"Password1!")
db.session.add(user)

# The first Rotation is always the default
db.session.add(Rotation(u"None"))
map(db.session.add, map(Rotation, [u"Metal", u"New Music", u"Jazz", u"Rock", u"Americana"]))

db.session.commit()
