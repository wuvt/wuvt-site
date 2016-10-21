from flask import Blueprint

bp = Blueprint('trackman', __name__)
private_bp = Blueprint('trackman_private', __name__)
api_bp = Blueprint('trackman_api', __name__)

from . import admin_views, cli, views
from .api import api
from .views import trackinfo
