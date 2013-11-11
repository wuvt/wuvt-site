from flask import abort, flash, jsonify, render_template, \
        render_template_string, redirect, request, url_for, Response, session
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import email.utils
import datetime
import json
import redis
import smtplib
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
    return render_template('admin/trackman_login.html',
            trackman_name=app.config['TRACKMAN_NAME'],
            automation=automation, djs=djs)


@app.route('/trackman/automation/start', methods=['POST'])
def trackman_start_automation():
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    red = redis.StrictRedis()
    red.set('automation_enabled', "true")

    return redirect(url_for('trackman_login'))


@app.route('/trackman/log/<int:setid>', methods=['GET', 'POST'])
def trackman_log(setid):
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    djset = DJSet.query.get_or_404(setid)
    errors = {}

    if 'artist' in request.form:
        session['email_playlist'] = 'email_playlist' in request.form

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

    if 'email_playlist' in session:
        email_playlist = session['email_playlist']
    else:
        email_playlist = False

    tracks = Track.query.filter(Track.djset_id == djset.id).\
            order_by(Track.datetime).all()

    return render_template('admin/trackman_log.html',
            trackman_name=app.config['TRACKMAN_NAME'], djset=djset,
            tracks=tracks, email_playlist=email_playlist, errors=errors)


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

    return render_template('admin/trackman_edit.html',
            trackman_name=app.config['TRACKMAN_NAME'], djset=djset,
            track=track, errors=errors)


@app.route('/trackman/log/<int:setid>/end', methods=['POST'])
def trackman_logout(setid):
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    djset = DJSet.query.get_or_404(setid)
    djset.dtend = datetime.datetime.now()
    db.session.commit()

    # email playlist
    if 'email_playlist' in session and session['email_playlist']:
        msg = MIMEMultipart('alternative')
        msg['Date'] = email.utils.formatdate()
        msg['From'] = app.config['MAIL_FROM']
        msg['To'] = djset.dj.email
        msg['Message-Id'] = email.utils.make_msgid()
        msg['X-Mailer'] = "Trackman"
        msg['Subject'] = "[{name}] {djname} - Playlist from {dtend}".format(
            name=app.config['TRACKMAN_NAME'],
            djname=djset.dj.airname,
            dtend=datetime.datetime.strftime(djset.dtend, "%Y-%m-%d"))

        tracks = Track.query.filter(Track.djset_id == djset.id).all()

        msg.attach(MIMEText(
            render_template('email/playlist.txt',
                            djset=djset, tracks=tracks).encode('utf-8'),
            'text'))
        msg.attach(MIMEText(
            render_template('email/playlist.html',
                            djset=djset, tracks=tracks).encode('utf-8'),
            'html'))

        s = smtplib.SMTP(app.config['SMTP_SERVER'])
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()

    session['email_playlist'] = False

    return redirect(url_for('trackman_login'))


@app.route('/trackman/register', methods=['GET', 'POST'])
def trackman_register():
    if not request.remote_addr in netaddr.IPSet(app.config['INTERNAL_IPS']):
        abort(403)

    errors = {}

    if request.method == 'POST':
        airname = request.form['airname'].strip()
        if len(airname) <= 0:
            errors['airname'] = "You must enter an on-air name."

        name = request.form['name'].strip()
        if len(name) <= 0:
            errors['name'] = "You must enter your name."

        email = request.form['email'].strip()
        if len(email) <= 0:
            errors['email'] = "You must enter your email address."

        phone = request.form['phone'].strip()
        if len(phone) <= 0:
            errors['phone'] = "You must enter your phone number."

        genres = request.form['genres'].strip()
        if len(genres) <= 0:
            errors['genres'] = "You must enter the genres you can DJ."

        if len(errors.items()) <= 0:
            newdj = DJ(airname, name)
            newdj.email = email
            newdj.phone = phone
            newdj.genres = genres
            db.session.add(newdj)
            db.session.commit()

            flash("DJ added")
            return redirect(url_for('trackman_login'))

    return render_template('admin/trackman_register.html',
            trackman_name=app.config['TRACKMAN_NAME'], errors=errors)
