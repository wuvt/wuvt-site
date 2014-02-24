from flask import Blueprint

bp = Blueprint('trackman', __name__)

from wuvt.trackman import admin_views
