from flask import Blueprint

bp = Blueprint('admin', __name__)

from wuvt.admin import views
from wuvt import app
from wuvt import format_datetime

@app.context_processor
def utility_processor():
    def format_price(amount, currency='$'):
        return u'{1}{0:.2f}'.format(amount/100, currency)
    return dict(format_price=format_price, format_datetime=format_datetime)
