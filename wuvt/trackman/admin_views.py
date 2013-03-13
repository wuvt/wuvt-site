from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
import datetime
import json
import redis
import netaddr

from wuvt import app
from wuvt import db
from wuvt import lib
from wuvt.trackman.lib import log_track
from wuvt.trackman.models import DJ, DJSet, Track


@app.route('/trackman', methods=['GET', 'POST'])
def trackman_login():
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    red = redis.StrictRedis()

    if 'dj' in request.form:
        red.set("automation_enabled", "false")

        dj = DJ.query.get(request.form['dj'])
        djset = DJSet(dj.id)
        db.session.add(djset)
        db.session.commit()

        return redirect(url_for('trackman_log', setid=djset.id))

    automation = red.get('automation_enabled') == "true"

    djs = DJ.query.filter(DJ.visible == True).order_by(DJ.airname).all()
    return render_template('admin/trackman_login.html', automation=automation,
            djs=djs)


@app.route('/trackman/automation/start', methods=['POST'])
def trackman_start_automation():
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    red = redis.StrictRedis()
    red.set('automation_enabled', "true")

    #flash("Automation started")
    return redirect(url_for('trackman_login'))


@app.route('/trackman/log/<int:setid>', methods=['GET', 'POST'])
def trackman_log(setid):
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    djset = DJSet.query.get_or_404(setid)
    errors = {}

    if 'artist' in request.form:
        artist = request.form['artist'].strip()
        if len(artist) <= 0:
            errors['artist'] = "You must enter an artist."

        title = request.form['title'].strip()
        if len(title) <= 0:
            errors['title'] = "You must enter a song title."

        album = request.form['album'].strip()
        if len(album) <= 0:
            errors['album'] = "You must enter an album."

        label = request.form['label'].strip()
        if len(label) <= 0:
            errors['label'] = "You must enter a label."

        if len(errors.items()) <= 0:
            log_track(djset.dj_id, djset.id, title, artist, album, label,
                    'request' in request.form, 'vinyl' in request.form)

    tracks = Track.query.filter(Track.djset_id == djset.id).\
            order_by(Track.datetime).all()

    return render_template('admin/trackman_log.html', djset=djset,
            tracks=tracks, errors=errors)


@app.route('/trackman/log/<int:setid>/<int:trackid>',
        methods=['DELETE', 'GET', 'POST'])
def trackman_edit(setid, trackid):
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    djset = DJSet.query.get_or_404(setid)
    track = Track.query.get_or_404(trackid)
    if track.djset_id != djset.id:
        abort(404)

    errors = {}

    if request.method == 'DELETE':
        db.session.delete(track)
        db.session.commit()
        return Response("deleted")
    elif request.method == 'POST':
        artist = request.form['artist'].strip()
        if len(artist) <= 0:
            errors['artist'] = "You must enter an artist."

        title = request.form['title'].strip()
        if len(title) <= 0:
            errors['title'] = "You must enter a song title."

        album = request.form['album'].strip()
        if len(album) <= 0:
            errors['album'] = "You must enter an album."

        label = request.form['label'].strip()
        if len(label) <= 0:
            errors['label'] = "You must enter a label."

        if len(errors.items()) <= 0:
            track.artist = artist
            track.title = title
            track.album = album
            track.label = label
            track.request = 'request' in request.form
            track.vinyl = 'vinyl' in request.form
            db.session.commit()

            return redirect(url_for('trackman_log', setid=djset.id))

    return render_template('admin/trackman_edit.html', djset=djset,
            track=track, errors=errors)


@app.route('/trackman/log/<int:setid>/end', methods=['POST'])
def trackman_logout(setid):
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    djset = DJSet.query.get_or_404(setid)
    djset.dtend = datetime.datetime.now()
    db.session.commit()

    return redirect(url_for('trackman_login'))
