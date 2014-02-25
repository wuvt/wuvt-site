from flask import Blueprint

bp = Blueprint('admin', __name__)

from wuvt.admin import views
