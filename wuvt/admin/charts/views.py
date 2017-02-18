from flask import render_template, request, send_file
import csv
import dateutil.parser
import io

from wuvt import app
from wuvt import auth_manager
from wuvt import format_datetime
from wuvt.admin import bp
from wuvt.trackman.models import TrackLog


@bp.route('/charts')
@auth_manager.check_access('library')
def charts_index():
    return render_template('admin/charts_index.html')


@bp.route('/charts/bmi', methods=['GET', 'POST'])
@auth_manager.check_access('library')
def charts_bmi():
    if request.method == 'POST':
        start = dateutil.parser.parse(request.form['dtstart'])
        end = dateutil.parser.parse(request.form['dtend'])
        end = end.replace(hour=23, minute=59, second=59)

        f = io.BytesIO()
        writer = csv.writer(f)

        tracks = TrackLog.query.filter(TrackLog.played >= start,
                                       TrackLog.played <= end).all()
        for track in tracks:
            writer.writerow([
                app.config['TRACKMAN_NAME'],
                format_datetime(track.played),
                track.track.title.encode("utf8"),
                track.track.artist.encode("utf8")])

        f.seek(0)

        filename = end.strftime("bmirep-%Y-%m-%d.csv")
        return send_file(f, mimetype="text/csv", as_attachment=True,
                         attachment_filename=filename)
    else:
        return render_template('admin/charts_bmi.html')
