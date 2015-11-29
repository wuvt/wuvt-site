#!/usr/bin/python2

from sqlalchemy.engine import create_engine
from wuvt import db
from wuvt.trackman.models import DJ, DJSet, Rotation, TrackLog, Track
import datetime
import pytz
import config


engine = create_engine(config.QUICKTRACK_DB_URI)
conn = engine.connect()

manual_djs = [
    u"Adam Capuano",
    u"Alex Field",
    u"Amanda Wade",
    u"Aydin Akyurtlu (subbing for Onur)",
    u"Brown Bear",
    u"Butterbeans",
    u"Corey",
    u"Greek Show 24 Nov",
    u"HHD",
    u"Jason Johnson",
    u"Jaymes Camery",
    u"Jevon Fournillier",
    u"John Gaskins & Jason Berrie",
    u"Julianna Wind",
    u"Julie McBulie",
    u"Left Off the Dial",
    u"Leon Phelps",
    u"mere",
    u"Richard Umemoto",
    u"Thomas Jackson Sakach, Esq.",
    u"Tom Porter",
    u"Tony Technotronic",
    u"Trackmaster Shaft",
    u"Vassili",
    u"Yemi and Julie",
    u"Yener Kutluay",
]
airname_map = {
    "Promised Hero": u"DJ Promised Hero",
    "\"The Don\"": u"The Don",
    "Maria": u"Maria Hatzios",
    "Thomson & Thompson": u"Thompson and Thomson",
    "The Wiggity Whack Swaggy Stack Show": u"The Wiggity Wack Swaggy Stack Show",
    "Captain Deaf Jean and the 43rd Vinyl-Scrounging Squirrel Battalion": u"Captain Deaf Jean and the 43rd Vinyl Scrounging Squirrel Battalion",
}
djname_map = {
    "'full' nelson bandana": "Full Nelson Bandana",
    "billygoat's hoedown": "BillyGoat",
    "chris klepper, greek show": "Chris Klepper",
    "deb sim/hickory dickory doc show": "hickory dickory dock show",
    "dj lo (laurel)": "DJ Lo",
    "gaskins": "John Gaskins",
    "hickory ": "hickory dickory dock show",
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
        'AMERICANA': u"Americana",
        'NEW_H': u"New Music",
        'NEW_M': u"New Music",
        'NEW_L': u"New Music",
        'METAL': u"Metal",
        'JAZZ': u"Jazz",
    }

    if rot in rotation_map:
        return Rotation.query.filter_by(rotation=rotation_map[rot]).first()
    else:
        return None


def find_or_insert_track(title, artist, album, label):
    title = title.strip()
    artist = artist.strip()
    album = album.strip()
    label = label.strip()

    # set label to "Not Available" if it is empty
    if len(label) <= 0:
        label = u"Not Available"

    existing = Track.query.filter(Track.title == title,
                                  Track.artist == artist,
                                  Track.album == album,
                                  Track.label == label).first()
    if existing is None:
        track = Track(title, artist, album, label)
        track.added = playedtime
        db.session.add(track)
        db.session.commit()
    else:
        track = existing

    return track


def make_djset(dj_id, dtstart):
    djset = DJSet(dj_id)
    djset.dtstart = dtstart
    db.session.add(djset)
    db.session.commit()
    return djset

local = pytz.timezone("America/New_York")


for airname in manual_djs:
    existing = DJ.query.filter(DJ.airname == airname).first()
    if existing is None:
        dj = DJ(airname, airname)
        dj.visible = False
        db.session.add(dj)
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
        dj.time_added = local.localize(r['dtTimeAdded'],
                                       is_dst=False).astimezone(pytz.utc)
        dj.visible = False
        db.session.add(dj)
        db.session.commit()
    else:
        dj = existing

    if r['vcAirName'] is not None:
        dj_id_map[r['vcAirName'].lower()] = dj.id
    dj_id_map[name.lower()] = dj.id

open_djset = None
playedtime = None
result = conn.execute('select * from quicktrack')
for r in result:
    print(r['biTrackID'])
    djname = r['vcDJName']
    is_new = r['enBin'] in ('NEW_H', 'NEW_M', 'NEW_L')
    rotation = get_rotation(r['enBin'])
    playedtime = local.localize(r['dtDateTime'],
                                is_dst=False).astimezone(pytz.utc)

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

    track = find_or_insert_track(r['vcTitle'], r['vcArtist'], r['vcAlbum'],
                                 r['vcLabel'])

    if open_djset is not None:
        djset = DJSet.query.get(open_djset)
        if djset.dj_id != dj_id:
            djset.dtend = playedtime
            db.session.commit()

            djset = make_djset(dj_id, playedtime)
    else:
        djset = make_djset(dj_id, playedtime)

    open_djset = djset.id
    tracklog = TrackLog(track.id, djset.id, r['boolRequest'], r['boolVinyl'],
                        is_new, rotation, r['intListeners'])
    tracklog.played = playedtime
    db.session.add(tracklog)
    db.session.commit()

if open_djset is not None and playedtime is not None:
    # close the open DJSet
    djset = DJSet.query.get(open_djset)
    djset.dtend = playedtime + datetime.timedelta(minutes=5)
    db.session.commit()
