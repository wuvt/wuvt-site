from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError, validators
from .lib import strip_field
from .models import DJ


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
