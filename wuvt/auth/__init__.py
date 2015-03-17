from flask import Blueprint

from wuvt import login_manager
from wuvt.models import User

bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


from wuvt.auth import views
