import stripe
from flask import render_template, request, Response
from wuvt import app
from wuvt import db
from wuvt.donate import bp
from wuvt.donate.models import Order


@bp.route('/')
def donate():
    return render_template('donate/premium_form.html')


@bp.route('/process', methods=['POST'])
def process():
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    premiums = request.form.get('premiums', 'no')
    amount = int(float(request.form['amount']) * 100)
    recurring = request.form.get('recurrence', 'once') == 'monthly'

    order = Order(request.form['name'], request.form['email'],
                  request.form.get('show', ''),
                  request.form.get('onair', 'n') == 'y',
                  request.form.get('firsttime', 'n') == 'y',
                  amount, recurring)

    if premiums != "no":
        order.set_premiums(premiums,
                           request.form.get('tshirtsize', None),
                           request.form.get('tshirtcolor', None),
                           request.form.get('sweatshirtsize', None),
                           request.form.get('sweatshirtcolor', None))

    if premiums == "ship":
        # add shipping cost, if our order exceeds the minimum amount for
        # shipping cost (e.g., lowest tier has free shipping)
        if amount >= app.config['DONATE_SHIPPING_MINIMUM']:
            amount += int(app.config['DONATE_SHIPPING_COST']) * 100

        order.set_address(request.form['address_1'], request.form['address_2'],
                          request.form['city'], request.form['state'],
                          request.form['zipcode'])

    if recurring:
        # create the plan
        stripe.Plan.create(
            amount=order.amount,
            interval="month",
            name=order.name,
            currency='usd',
            statement_description=app.config['STRIPE_DESCRIPTION'],
            id=str(order.id)
        )

        # create the customer using stripe_token
        customer = stripe.Customer.create(
            card=request.form['stripe_token'],
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
                source=request.form['stripe_token'],
                description="Order #{}".format(order.id))
        except stripe.CardError, e:
            return Response("Your card was declined. Please try again with "\
                            "a different method of payment.")

        order.set_paid('stripe')

    db.session.add(order)
    db.session.commit()

    # TODO: send thank you email

    return Response("Thanks for your order.")


@bp.route('/thanks')
def thanks():
    return render_template('donate/thanks.html')
