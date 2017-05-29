from flask import current_app
from flask_wtf import FlaskForm
from wtforms import BooleanField, StringField, ValidationError, validators
from .view_utils import slugify


def strip_field(val):
    if isinstance(val, basestring):
        return val.strip()
    else:
        return val


def slugify_field(val):
    if isinstance(val, basestring):
        return slugify(val)
    else:
        return val


class PageForm(FlaskForm):
    title = StringField('Title', filters=[strip_field],
                        validators=[validators.Length(min=1, max=255),
                                    validators.DataRequired()])
    slug = StringField('Slug', filters=[slugify_field])
    section = StringField('Section', validators=[validators.DataRequired()])
    published = BooleanField('Published', default=False)
    content = StringField('Content', filters=[strip_field],
                          validators=[validators.DataRequired()])

    def validate_section(self, field):
        for section in current_app.config['NAV_TOP_SECTIONS']:
            if section['menu'] == field.data:
                return

        raise ValidationError("The specified section must exist.")
