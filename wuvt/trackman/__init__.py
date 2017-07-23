from flask import Blueprint

bp = Blueprint('trackman', __name__)
private_bp = Blueprint('trackman_private', __name__)
api_bp = Blueprint('trackman_api', __name__)

from .cache import ResourceCache
playlists_cache = ResourceCache(config={
    'CACHE_KEY_PREFIX': "trackman_playlists_",
})
charts_cache = ResourceCache(config={
    'CACHE_DEFAULT_TIMEOUT': 14400,
    'CACHE_KEY_PREFIX': "trackman_charts_",
})

from . import admin_views, cli, views
from .api import api
from .views import trackinfo
