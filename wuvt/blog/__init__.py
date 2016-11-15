from flask import Blueprint

SUMMARY_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'br',
    'code',
    'div',
    'em',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'i',
    'img',
    'li',
    'ol',
    'p',
    'strong',
    'ul',
]

SUMMARY_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title'],
    'div': ['class', 'style'],
    'h1': ['class', 'style'],
    'h2': ['class', 'style'],
    'h3': ['class', 'style'],
    'h4': ['class', 'style'],
    'h5': ['class', 'style'],
    'h6': ['class', 'style'],
    'img': ['alt', 'src', 'title'],
}

SUMMARY_ALLOWED_STYLES = ['color', 'clear', 'text-align']

bp = Blueprint('blog', __name__)

from . import views
