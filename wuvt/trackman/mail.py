from datetime import datetime
from flask import current_app, render_template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
import smtplib
from .. import format_datetime


def send_logout_reminder(dj):
    msg = MIMEText(render_template('email/logout_reminder.txt',
                                   dj=dj).encode('utf-8'))
    msg['Date'] = email.utils.formatdate()
    msg['From'] = current_app.config['MAIL_FROM']
    msg['To'] = dj.email
    msg['Message-Id'] = email.utils.make_msgid()
    msg['X-Mailer'] = "Trackman"
    msg['Subject'] = "[{name}] Logout Reminder".format(
        name=current_app.config['TRACKMAN_NAME'])

    try:
        s = smtplib.SMTP(current_app.config['SMTP_SERVER'])
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()
    except Exception as exc:
        current_app.logger.warning(
            "Trackman: Failed to send logout reminder to DJ {0}: {1}".format(
                dj.id, exc))


def send_playlist(djset, tracks):
    msg = MIMEMultipart('alternative')
    msg['Date'] = email.utils.formatdate()
    msg['From'] = current_app.config['MAIL_FROM']
    msg['To'] = djset.dj.email
    msg['Message-Id'] = email.utils.make_msgid()
    msg['X-Mailer'] = "Trackman"
    msg['Subject'] = "[{name}] {djname} - Playlist from {dtend}".format(
        name=current_app.config['TRACKMAN_NAME'],
        djname=djset.dj.airname,
        dtend=format_datetime(djset.dtend, "%Y-%m-%d"))

    msg.attach(MIMEText(
        render_template('email/playlist.txt',
                        djset=djset, tracks=tracks).encode('utf-8'),
        'plain'))
    msg.attach(MIMEText(
        render_template('email/playlist.html',
                        djset=djset, tracks=tracks).encode('utf-8'),
        'html'))

    try:
        s = smtplib.SMTP(current_app.config['SMTP_SERVER'])
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()
    except Exception as exc:
        current_app.logger.warning(
            "Trackman: Failed to send email for DJ set {0}: {1}".format(
                djset.id, exc))


def send_chart(chart):
    msg = MIMEMultipart('alternative')
    msg['Date'] = email.utils.formatdate()
    msg['From'] = current_app.config['MAIL_FROM']
    msg['To'] = current_app.config['CHART_MAIL_DEST']
    msg['Message-Id'] = email.utils.make_msgid()
    msg['X-Mailer'] = "Trackman"
    timestamp = datetime.utcnow()
    msg['Subject'] = "[{name}] New Music Chart {timestamp}".format(
        name=current_app.config['TRACKMAN_NAME'],
        timestamp=format_datetime(timestamp, "%Y-%m-%d"))

    msg.attach(MIMEText(
        render_template('email/new_chart.txt',
                        chart=chart, timestamp=timestamp).encode('utf-8'),
        'plain'))
    try:
        s = smtplib.SMTP(current_app.config['SMTP_SERVER'])
        s.sendmail(msg['From'], [msg['To']], msg.as_string())
        s.quit()
    except Exception as exc:
        current_app.logger.warning(
            "Trackman: Failed to send weekly chart - {0}".format(exc))
