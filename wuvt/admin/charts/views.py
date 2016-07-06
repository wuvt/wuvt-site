from flask import render_template, request, url_for, send_file
import dateutil.parser
import io

from wuvt import app
from wuvt import db
from wuvt.admin import bp
from wuvt.auth import check_access
from wuvt.trackman.models import TrackLog


@bp.route('/charts')
@check_access('library')
def charts_index():
    return render_template('admin/charts_index.html')


@bp.route('/charts/bmi', methods=['GET', 'POST'])
@check_access('library')
def charts_bmi():
    if request.method == 'POST':
        start = dateutil.parser.parse(request.form['dtstart'])
        end = dateutil.parser.parse(request.form['dtend'])
        end = end.replace(hour=23, minute=59, second=59)

        f = io.BytesIO()

        tracks = TrackLog.query.filter(TrackLog.played >= start,
                                       TrackLog.played <= end).all()
        for track in tracks:
            f.write(','.join([app.config['TRACKMAN_NAME'],
                              format_datetime(track.played),
                              track.track.title.encode("utf8"),
                              track.track.artist.encode("utf8")]) + "\n")

        filename = end.strftime("bmirep-%Y-%m-%d.csv")
        return send_file(f, mimetype="text/csv", as_attachment=True,
                         attachment_filename=filename)
    else:
        return render_template('admin/charts_bmi.html')
