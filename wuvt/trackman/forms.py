from flask import current_app
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, \
    ValidationError, validators
from .models import DJ


def strip_field(val):
    if isinstance(val, basestring):
        return val.strip()
    else:
        return val


def artist_validate(form, field):
    if field.data in current_app.config['TRACKMAN_ARTIST_PROHIBITED']:
        raise ValidationError("That artist may not be entered.")


def label_validate(form, field):
    if field.data in current_app.config['TRACKMAN_LABEL_PROHIBITED']:
        raise ValidationError("That label may not be entered.")


class DJRegisterForm(FlaskForm):
    airname = StringField('On-air Name', filters=[strip_field],
                          validators=[validators.Length(min=1, max=255),
                                      validators.DataRequired()])
    name = StringField('Real Name', filters=[strip_field],
                       validators=[validators.Length(min=1, max=255),
                                   validators.DataRequired()])
    email = StringField('Email Address', filters=[strip_field],
                        validators=[validators.Length(min=1, max=255),
                                    validators.Email(),
                                    validators.DataRequired()])
    phone = StringField('Phone Number', filters=[strip_field],
                        validators=[validators.Length(min=10, max=12),
                                    validators.DataRequired()])
    genres = StringField('Genres you can DJ', filters=[strip_field],
                         validators=[validators.Length(min=1, max=255),
                                     validators.DataRequired()])

    def validate_airname(self, field):
        matching = DJ.query.filter(DJ.airname == field.data).count()
        if matching > 0:
            raise ValidationError("Your on-air name must be unique.")


class DJReactivateForm(FlaskForm):
    email = StringField('Email Address', filters=[strip_field],
                        validators=[validators.Length(min=1, max=255),
                                    validators.Email(),
                                    validators.DataRequired()])
    phone = StringField('Phone Number', filters=[strip_field],
                        validators=[validators.Length(min=10, max=12),
                                    validators.DataRequired()])


class TrackAddForm(FlaskForm):
    title = StringField('Title', filters=[strip_field],
                        validators=[validators.DataRequired()])
    artist = StringField('Artist', filters=[strip_field],
                         validators=[artist_validate,
                                     validators.DataRequired()])
    album = StringField('Album', filters=[strip_field],
                        validators=[validators.DataRequired()])
    label = StringField('Label', filters=[strip_field],
                        validators=[label_validate,
                                    validators.DataRequired()])


class AutomationTrackLogForm(FlaskForm):
    password = StringField('Password')
    title = StringField('Title', filters=[strip_field])
    artist = StringField('Artist', filters=[strip_field])
    album = StringField('Album', filters=[strip_field])
    label = StringField('Label', filters=[strip_field])


class TrackLogEditForm(FlaskForm):
    title = StringField('Title', filters=[strip_field],
                        validators=[validators.DataRequired()])
    artist = StringField('Artist', filters=[strip_field],
                         validators=[artist_validate,
                                     validators.DataRequired()])
    album = StringField('Album', filters=[strip_field],
                        validators=[validators.DataRequired()])
    label = StringField('Label', filters=[strip_field],
                        validators=[label_validate,
                                    validators.DataRequired()])
    request = BooleanField('Request')
    vinyl = BooleanField('Vinyl')
    new = BooleanField('New')
    rotation = IntegerField('Rotation', default=1)
    played = StringField('Played')


class TrackLogForm(FlaskForm):
    track_id = IntegerField('Track ID')
    djset_id = IntegerField('DJSet ID')
    request = BooleanField('Request')
    vinyl = BooleanField('Vinyl')
    new = BooleanField('New')
    rotation = IntegerField('Rotation', default=1)
    played = StringField('Played')


class AirLogEditForm(FlaskForm):
    airtime = StringField('Air Time')
    logtype = IntegerField('Log Type', default=0)
    logid = IntegerField('Log ID', default=0)


class AirLogForm(FlaskForm):
    djset_id = IntegerField('DJSet ID')
    airtime = StringField('Air Time')
    logtype = IntegerField('Log Type', default=0)
    logid = IntegerField('Log ID', default=0)
