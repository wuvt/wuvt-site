#!/usr/bin/python2

from sqlalchemy.engine import create_engine
from wuvt import db
from wuvt.trackman.models import DJ, DJSet, Rotation, TrackLog, Track
import config


engine = create_engine(config.QUICKTRACK_DB_URI)
conn = engine.connect()

manual_djs = {
    "Adam Capuano",
    "Alex Field",
    "Amanda Wade",
    "Aydin Akyurtlu (subbing for Onur)",
    "Brown Bear",
    "Butterbeans",
    "Corey",
    "Greek Show 24 Nov",
    "HHD",
    "Jason Johnson",
    "Jaymes Camery",
    "Jevon Fournillier",
    "John Gaskins & Jason Berrie",
    "Julianna Wind",
    "Julie McBulie",
    "Left Off the Dial",
    "Leon Phelps",
    "mere",
    "Richard Umemoto",
    "Thomas Jackson Sakach, Esq.",
    "Tom Porter",
    "Tony Technotronic",
    "Trackmaster Shaft",
    "Vassili",
    "Yemi and Julie",
    "Yener Kutluay",
}
airname_map = {
    "Promised Hero": "DJ Promised Hero",
    "\"The Don\"": "The Don",
    "Maria": "Maria Hatzios",
}
djname_map = {
    "'full' nelson bandana": "Full Nelson Bandana",
    "billygoat's hoedown": "BillyGoat",
    "chris klepper, greek show": "Chris Klepper",
    "deb sim/hickory dickory doc show": "hickory dickory dock show",
    "dj lo (laurel)": "DJ Lo",
    "gaskins": "John Gaskins",
    "hickory": "hickory dickory dock show",
    "hickory dickory doc show": "hickory dickory dock show",
    "the hickory dickory dock show": "hickory dickory dock show",
    "maria hatzios--greek show": "Maria Hatzios",
    "maria hatzios---greek show": "Maria Hatzios",
    "martia hatzios-greek show": "Maria Hatzios",
    "pete french": "Pete",
    "ramage": "Ramage Mendez",
    "steve b": "steve b.",
    "martia hatzios": "Maria Hatzios",
    "ace fever": "commodore ace fever",
    "m@t sherman": "Matthew Danger Sherman",
    "mike matthews": "Michael Matthews",
    "yemingtong steele": "Yemington Steele",
    "yener kutluay (cont'd)": "Yener Kutluay",
    "jevon foutnillier": "Jevon Fournillier",
    "thomas jackson sakach": "Thomas Jackson Sakach, Esq.",
    "thomas jackson sakach iii": "Thomas Jackson Sakach, Esq.",
    "t. jackson sakach": "Thomas Jackson Sakach, Esq.",
    "tom sakach": "Thomas Jackson Sakach, Esq.",
}
dj_id_map = {}


def get_rotation(rot):
    rotation_map = {
        'AMERICANA': "Americana",
        'NEW_H': "New Music",
        'NEW_M': "New Music",
        'NEW_L': "New Music",
        'METAL': "Metal",
        'JAZZ': "Jazz",
    }

    if rot in rotation_map:
        return Rotation.query.filter_by(rotation=rotation_map[rot]).first()
    else:
        return None


def make_djset(dj_id, dtstart):
    djset = DJSet(dj_id)
    djset.dtstart = dtstart
    db.session.add(djset)
    db.session.commit()
    return djset


for airname in manual_djs:
    existing = DJ.query.filter(DJ.airname == airname).first()
    if existing is None:
        dj = DJ(airname, airname)
        dj.visible = False
        dj.session.add(dj)
        db.session.commit()
    else:
        dj = existing

    dj_id_map[airname.lower()] = dj.id

result = conn.execute('select * from quicktrack_users')
for r in result:
    name = " ".join([r['vcFirstName'], r['vcLastName']])
    airname = r['vcAirName']

    if name.lower() == "testy mctesterson":
        # don't import test entries
        continue
    elif airname is None:
        # use name if DJ doesn't have an airname
        airname = name
    elif airname in airname_map:
        airname = airname_map[airname]

    existing = DJ.query.filter(DJ.airname == airname).first()
    if existing is None:
        dj = DJ(airname, name)
        dj.phone = r['vcPhoneNum']
        dj.email = r['vcEmail']
        dj.genres = r['vcGenres']
        dj.time_added = r['dtTimeAdded']
        dj.visible = False
        db.session.add(dj)
        db.session.commit()
    else:
        dj = existing

    if r['vcAirName'] is not None:
        dj_id_map[r['vcAirName'].lower()] = dj.id
    dj_id_map[name.lower()] = dj.id

open_djset = None
result = conn.execute('select * from quicktrack')
for r in result:
    djname = r['vcDJName']
    is_new = r['enBin'] in ('NEW_H', 'NEW_M', 'NEW_L')
    rotation = get_rotation(r['enBin'])

    if djname.lower() in djname_map:
        djname = djname_map[djname.lower()]
    elif djname.lower() in ("testy mctesterson",
                            "'full' nelson bandana (test)"):
        # don't import test entries
        continue

    if djname == "Automation":
        dj_id = 1
    elif djname.lower() in dj_id_map:
        dj_id = dj_id_map[djname.lower()]
    else:
        print("Need a DJ ID for {}".format(djname))
        with open('bad_djs.txt', 'a') as f:
            f.write("{}\n".format(djname))
        continue

    track = Track(r['vcTitle'], r['vcArtist'], r['vcAlbum'], r['vcLabel'])
    track.added = r['dtDateTime']

    # set label to "Not Available" if it is empty
    if len(track.label) <= 0:
        track.label = u"Not Available"

    db.session.add(track)
    db.session.commit()

    if open_djset is not None:
        djset = DJSet.query.get(open_djset)
        if djset.dj_id != dj_id:
            djset.dtend = r['dtDateTime']
            db.session.commit()

            djset = make_djset(dj_id, r['dtDateTime'])
    else:
        djset = make_djset(dj_id, r['dtDateTime'])

    open_djset = djset.id
    tracklog = TrackLog(track.id, djset.id, r['boolRequest'], r['boolVinyl'],
                        is_new, rotation, r['intListeners'])
    tracklog.played = r['dtDateTime']
    db.session.add(tracklog)
    db.session.commit()
