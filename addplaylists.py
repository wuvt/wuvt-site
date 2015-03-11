#!/usr/bin/env python2
from datetime import datetime
from datetime import timedelta
import random
from wuvt.trackman.lib import perdelta
from wuvt import db
from wuvt.trackman.models import DJSet, DJ

today = datetime.now()
print("adding dj")
dj = DJ(u"Johnny 5", u"John")
db.session.add(dj)
db.session.commit()

print("djadded")
for show in perdelta(today - timedelta(days=500), today, timedelta(hours=4)):
    if random.randint(0,99) < 40:
        djset = DJSet(dj.id)
        djset.dtstart = show
        djset.dtend = show + timedelta(4)
        db.session.add(djset)
        db.session.commit()

