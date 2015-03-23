from flask import render_template, request, Response
from wuvt import app
from wuvt.donate import bp
import stripe


@bp.route('/')
def donate():
    return render_template('donate/premium_form.html')


@bp.route('/process', methods=['POST'])
def process():
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    amount = float(request.form['amount']) * 100
    ship_premiums = request.form.get('ship_premiums', None) == "true"
    if ship_premiums:
        amount += int(app.config['DONATE_SHIPPING_COST']) * 100

    try:
        charge = stripe.Charge.create(
            amount=amount,
            currency="usd",
            source=request.form['stripe_token'],
            description=app.config['STRIPE_DESCRIPTION'])
    except stripe.CardError, e:
        int("Card declined!")
        print(e)

    # TODO: insert into database
    # TODO: send thank you email

    return Response("yes")
