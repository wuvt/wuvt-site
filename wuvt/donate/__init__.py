import stripe
from flask import Blueprint
from wuvt import app

bp = Blueprint('donate', __name__)

def process_stripe(order, stripe_token, amount):
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    if order.recurring:
        # create the plan
        stripe.Plan.create(
            amount=order.amount,
            interval="month",
            name=order.name,
            currency="usd",
            statement_description=app.config['STRIPE_DESCRIPTION'],
            id=str(order.id)
        )

        # create the customer using stripe_token
        customer = stripe.Customer.create(
            card=stripe_token,
            email=order.email
        )

        order.custid = customer.id

        # bill for shipping, if applicable
        if premiums == "ship":
            stripe.InvoiceItem.create(
                customer=order.custid,
                amount=int(app.config['DONATE_SHIPPING_COST']) * 100,
                currency="usd",
                description="One-time shipping fee")

        # create the subscription
        cust = stripe.Customer.retrieve(order.custid)
        cust.subscriptions.create(plan=str(order.id))
    else:
        try:
            # charge the customer using stripe_token
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=stripe_token,
                description="Order #{}".format(order.id))
        except stripe.CardError, e:
            return False

        order.set_paid('stripe')

    return True


from . import views
