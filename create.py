#!/usr/bin/python2

from wuvt import db
from wuvt.blog.models import Category
from wuvt.trackman.models import DJ

#db.drop_all()
db.create_all()

#dj = DJ("Automation", "Automation")
#db.session.add(dj)
#db.session.commit()

cats = [Category("News", "news"), Category("Sports", "sports"),
        Category("Weather", "weather"),
        Category("Woove", "woove")]
for cat in cats:
    db.session.add(cat)
db.session.commit()
