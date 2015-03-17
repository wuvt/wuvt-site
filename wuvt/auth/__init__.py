from flask import Blueprint

bp = Blueprint('auth', __name__)

from wuvt.auth import views
