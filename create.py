#!/usr/bin/python2

from wuvt import db
from wuvt.blog.models import Category
from wuvt.trackman.models import DJ

#db.drop_all()
db.create_all()

#dj = DJ("Automation", "Automation")
#db.session.add(dj)
#db.session.commit()

woove = Category("Woove", "woove")
db.session.add(woove)
db.session.commit()

cats = [Category("News", "news"), Category("Sports", "sports"),
        Category("Weather", "weather"),
        
        Category("Editorials", "editorials", woove.id),
        Category("Artist Profiles", "artist-profiles", woove.id),
        Category("DJ Bios", "dj-bios", woove.id),
        Category("Interviews", "interviews", woove.id),
        Category("Music Reviews", "music-reviews", woove.id),
        Category("Lists", "lists", woove.id),
        Category("Local Events", "local-events", woove.id),
        Category("Movie Reviews", "movie-reviews", woove.id),
        Category("Literary Contest", "literary-contents", woove.id)]
for cat in cats:
    db.session.add(cat)
db.session.commit()
