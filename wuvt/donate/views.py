import stripe
from flask import render_template, request, Response
from wuvt import app
from wuvt import db
from wuvt.donate import bp
from wuvt.donate.models import Order


@bp.route('/')
def donate():
    # TODO: we need to recurring donations separately
    return render_template('donate/premium_form.html')


@bp.route('/process', methods=['POST'])
def process():
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    premiums = request.form.get('premiums', 'no')

    amount = int(float(request.form['amount']) * 100)
    if premiums == "ship" and amount >= app.config['DONATE_SHIPPING_MINIMUM']:
        amount += int(app.config['DONATE_SHIPPING_COST']) * 100

    # FIXME: uncomment
    #try:
    #    charge = stripe.Charge.create(
    #        amount=amount,
    #        currency="usd",
    #        source=request.form['stripe_token'],
    #        description=app.config['STRIPE_DESCRIPTION'])
    #except stripe.CardError, e:
    #    int("Card declined!")
    #    print(e)

    order = Order(request.form['name'], request.form['email'],
                  request.form.get('show', ''),
                  request.form.get('onair', 'n') == 'y',
                  request.form.get('firsttime', 'n') == 'y',
                  amount,
                  request.form.get('recurrence', 'once') == 'monthly')

    if premiums != "no":
        order.set_premiums(premiums,
                           request.form.get('tshirtsize', None),
                           request.form.get('tshirtcolor', None),
                           request.form.get('sweatshirtsize', None),
                           request.form.get('sweatshirtcolor', None))

    if premiums == "ship":
        order.set_address(request.form['address_1'], request.form['address_2'],
                          request.form['city'], request.form['state'],
                          request.form['zipcode'])

    order.set_paid('stripe')

    db.session.add(order)
    db.session.commit()

    # TODO: send thank you email

    return Response("yes")
