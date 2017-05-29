from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, StringField, \
    ValidationError, validators
from .models import Category
from ..auth.models import User
from ..view_utils import slugify


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


class ArticleForm(FlaskForm):
    title = StringField('Title', filters=[strip_field],
                        validators=[validators.Length(min=1, max=255),
                                    validators.DataRequired()])
    slug = StringField('Slug', filters=[slugify_field])
    author_id = IntegerField('Author',
                             validators=[validators.DataRequired()])
    category_id = IntegerField('Category',
                               validators=[validators.DataRequired()])
    published = BooleanField('Published', default=False)
    front_page = BooleanField('Front Page', default=False)
    summary = StringField('Summary', filters=[strip_field],
                          validators=[validators.DataRequired()])
    content = StringField('Content', filters=[strip_field],
                          validators=[validators.DataRequired()])

    def validate_author_id(self, field):
        if User.query.filter_by(id=field.data).count() != 1:
            raise ValidationError("The specified author must exist.")

    def validate_category_id(self, field):
        if Category.query.filter_by(id=field.data).count() != 1:
            raise ValidationError("The specified category must exist.")
