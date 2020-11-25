import datetime
from wuvt import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(255))
    email = db.Column(db.Unicode(255))
    phone = db.Column(db.Unicode(12))
    placed_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    remote_addr = db.Column(db.Unicode(50))
    user_agent = db.Column(db.Unicode(255))
    dj = db.Column(db.UnicodeText)
    thank_on_air = db.Column(db.Boolean, default=False)
    first_time = db.Column(db.Boolean, default=True)
    donor_comment = db.Column(db.UnicodeText)

    premiums = db.Column(db.Unicode(255))               # mail, pickup, or none
    address1 = db.Column(db.Unicode(255))
    address2 = db.Column(db.Unicode(255))
    city = db.Column(db.Unicode(255))
    state = db.Column(db.Unicode(255))
    zipcode = db.Column(db.Integer)

    amount = db.Column(db.Integer)                      # amount charged (in US cents)
    recurring = db.Column(db.Boolean, unique=False, default=False)
    paid_date = db.Column(db.DateTime, default=None)
    shipped_date = db.Column(db.DateTime, default=None)

    tshirtsize = db.Column(db.Unicode(255))
    tshirtcolor = db.Column(db.Unicode(255))
    sweatshirtsize = db.Column(db.Unicode(255))

    method = db.Column(db.Unicode(255))
    custid = db.Column(db.Unicode(255))                 # used for Stripe recurrence
    comments = db.Column(db.UnicodeText)                # Internal use only. Staff can modify.

    def __init__(self, name, email, dj, thank_on_air, first_time, amount,
                 recurring):
        self.name = name
        self.email = email
        self.dj = dj
        self.thank_on_air = thank_on_air
        self.first_time = first_time
        self.amount = amount
        self.recurring = recurring

    def set_user_agent(self, user_agent):
        self.user_agent = str(user_agent)[:255]

    def set_premiums(self, premiums, tshirtsize, tshirtcolor, sweatshirtsize):
        self.premiums = premiums
        self.tshirtsize = tshirtsize
        self.tshirtcolor = tshirtcolor
        self.sweatshirtsize = sweatshirtsize

    def set_address(self, address1, address2, city, state, zipcode):
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.state = state
        self.zipcode = zipcode

    def set_paid(self, method, paid_date=None):
        self.method = method

        if paid_date is not None:
            self.paid_date = paid_date
        else:
            self.paid_date = datetime.datetime.utcnow()

    def set_shipped(self, shipped_date=None):
        if self.premiums is not None:
            # shipped & picked up are the same
            if shipped_date is not None:
                self.shipped_date = shipped_date
            else:
                self.shipped_date = datetime.datetime.utcnow()
