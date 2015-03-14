from flask import Blueprint

bp = Blueprint('donate', __name__)

from . import views
