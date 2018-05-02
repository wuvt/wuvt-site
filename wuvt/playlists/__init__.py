from flask import Blueprint

bp = Blueprint('playlists', __name__)

from . import views
from .views import trackinfo
