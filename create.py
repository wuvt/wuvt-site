#!/usr/bin/env python2

from wuvt import db
from wuvt.blog.models import Category
from wuvt.trackman.models import DJ, Track, Rotation
from wuvt.models import User

db.drop_all()

db.create_all()

dj = DJ("Automation", "Automation")
db.session.add(dj)
db.session.commit()




cats = [Category("News", "news"), Category("Sports", "sports"),
        Category("Weather", "weather"),
        Category("Woove", "woove")]
for cat in cats:
    db.session.add(cat)



# There must be a user called 'admin'. This is hardcoded in everything to be the superuser.
user = User("admin", "admin", "admin@wuvt.vt.edu")
user.set_password("test")
db.session.add(user)
# The first Rotation must be the default
db.session.add(Rotation("None"));
# Test data
db.session.add(Track('The Divine Conspiracy', 'Epica', 'The Divine Conspiracy', 'Avalon'))
db.session.add(Track('Second Stone', 'Epica', 'The Quantum Enigma', 'Nuclear Blast'))
map(db.session.add, map(Rotation, ["Metal", "New Music", "Jazz", "Rock", "Americana"]))

db.session.commit()
