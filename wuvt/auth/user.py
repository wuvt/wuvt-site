from wuvt import db
from wuvt.auth.models import User


def _find_or_create_user(username, name, email):
    user = User.query.filter(User.username == username).first()

    if user is None:
        # create new user in the database, since one doesn't already exist
        user = User(username, name, email)
        db.session.add(user)
    else:
        # update existing user data in database
        user.name = name
        user.email = email

    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise

    return user
