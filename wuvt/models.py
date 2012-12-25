from wuvt import db


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Unicode, nullable=False)
    name = db.Column(db.Unicode, nullable=False)

    def __init__(self, username, name):
        self.username = username
        self.name = name

