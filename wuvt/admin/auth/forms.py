from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError, validators
from wuvt import app
from wuvt.auth.models import User


def strip_field(val):
    if isinstance(val, str):
        return val.strip()
    else:
        return val


class UserAddForm(FlaskForm):
    username = StringField('Username', filters=[strip_field],
                           validators=[validators.Length(min=3, max=8),
                                       validators.Regexp(r'^[A-Za-z0-9]+'),
                                       validators.DataRequired()])
    name = StringField('Name', filters=[strip_field],
                       validators=[validators.Length(min=1, max=255),
                                   validators.DataRequired()])
    email = StringField('Email Address', filters=[strip_field],
                        validators=[validators.Length(min=1, max=255),
                                    validators.Email(),
                                    validators.DataRequired()])
    password = StringField('Password', filters=[strip_field], validators=[
        validators.Length(min=app.config['MIN_PASSWORD_LENGTH'], max=255),
        validators.DataRequired(),
    ])

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).count() > 0:
            raise ValidationError("The username must be unique.")


class UserEditForm(FlaskForm):
    name = StringField('Name', filters=[strip_field],
                       validators=[validators.Length(min=1, max=255),
                                   validators.DataRequired()])
    email = StringField('Email Address', filters=[strip_field],
                        validators=[validators.Length(min=1, max=255),
                                    validators.Email(),
                                    validators.DataRequired()])
    newpass = StringField('Password', filters=[strip_field], validators=[
        validators.Length(min=app.config['MIN_PASSWORD_LENGTH'], max=255),
        validators.Optional(),
    ])
