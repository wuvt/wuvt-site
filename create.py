#!/usr/bin/env python2

from wuvt import db
from wuvt.blog.models import Category
from wuvt.trackman.models import DJ
from wuvt.models import User

db.drop_all()

db.create_all()

#dj = DJ("Automation", "Automation")
#db.session.add(dj)
#db.session.commit()




#cats = [Category("News", "news"), Category("Sports", "sports"),
#        Category("Weather", "weather"),
#        Category("Woove", "woove")]
#for cat in cats:
#    db.session.add(cat)



# There must be a user called 'admin'. This is hardcoded in everything to be the superuser.
user = User("admin", "admin", "admin@wuvt.vt.edu")
user.set_password("test")
db.session.add(user)

db.session.commit()
