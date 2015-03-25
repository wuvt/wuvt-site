from flask import render_template, request, Response
from wuvt import app
from wuvt import auth
from wuvt import db
from wuvt.donate import bp
from wuvt.donate import process_stripe
from wuvt.donate.models import Order


@bp.route('/')
def donate():
    return render_template('donate/premium_form.html')


@bp.route('/process', methods=['POST'])
def process():
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

    if not process_stripe(order, request.form['stripe_token'], amount):
        return Response("Your card was declined. Please try again with "\
                        "a different method of payment.")

    db.session.add(order)
    db.session.commit()

    return Response("Thanks for your order.")


@bp.route('/thanks')
def thanks():
    return render_template('donate/thanks.html')


@bp.route('/missioncontrol', methods=['GET', 'POST'])
@auth.check_access('missioncontrol')
def missioncontrol_index():
    if 'amount' in request.form:
        print(request.form)

        premiums = request.form.get('premiums', 'no')
        amount = int(float(request.form['amount']) * 100)
        recurring = request.form.get('recurrence', 'once') == 'monthly'

        order = Order(request.form.get('name', ''),
                      request.form.get('email', ''),
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

        if not process_stripe(order, request.form['stripe_token'], amount):
            return Response("Your card was declined. Please try again with "\
                            "a different method of payment.")

        db.session.add(order)
        db.session.commit()


    return render_template('donate/missioncontrol/index.html')
