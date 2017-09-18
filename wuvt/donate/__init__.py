import stripe
from flask import Blueprint
from wuvt import app

bp = Blueprint('donate', __name__)


def get_plan(id):
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    return stripe.Plan.retrieve(id)


def list_plans():
    stripe.api_key = app.config['STRIPE_SECRET_KEY']
    return stripe.Plan.all()['data']


def process_stripe_onetime(order, stripe_token, amount):
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    try:
        # charge the customer using stripe_token
        charge = stripe.Charge.create(
            amount=amount,
            currency="usd",
            source=stripe_token,
            description="Order #{}".format(order.id))
    except stripe.CardError as e:
        return False

    return True


def process_stripe_recurring(order, stripe_token, plan, shipping_cost=0):
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    # create the customer using stripe_token
    try:
        customer = stripe.Customer.create(
            card=stripe_token,
            email=order.email
        )
    except stripe.CardError as e:
        return False

    order.custid = customer.id

    # bill for shipping, if applicable
    if shipping_cost > 0:
        stripe.InvoiceItem.create(
            customer=order.custid,
            amount=shipping_cost,
            currency="usd",
            description="One-time shipping fee")

    # create the subscription
    cust = stripe.Customer.retrieve(order.custid)
    cust.subscriptions.create(plan=plan)

    return True


from . import views
