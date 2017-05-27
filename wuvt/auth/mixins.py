class UserMixin(object):
    @property
    def is_authenticated(self):
        return True


class AnonymousUserMixin(object):
    @property
    def is_authenticated(self):
        return False
