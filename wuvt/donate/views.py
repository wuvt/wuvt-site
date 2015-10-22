import netaddr
from flask import abort, flash, make_response, render_template, request, \
        Response
from functools import wraps
from wuvt import app
from wuvt import auth
from wuvt import db
from wuvt.donate import bp
from wuvt.donate import get_plan, list_plans, process_stripe_onetime, \
        process_stripe_recurring
from wuvt.donate.models import Order


def local_only(f):
    @wraps(f)
    def local_wrapper(*args, **kwargs):
        if not request.remote_addr in \
                netaddr.IPSet(app.config['INTERNAL_IPS']):
            abort(403)
        else:
            return f(*args, **kwargs)
    return local_wrapper


@bp.route('/onetime')
def donate_onetime():
    return render_template('donate/premium_form.html')


@bp.route('/monthly')
def donate_recurring():
    plans = list_plans()
    plan_ids = [plan.id for plan in plans]

    return render_template('donate/recurring_form.html', plans=plans)


@bp.route('/process', methods=['POST'])
def process():
    premiums = request.form.get('premiums', 'no')
    shipping_cost = 0

    if 'plan' in request.form:
        recurring = True
        plan = get_plan(request.form['plan'])

        if plan:
            amount = plan.amount
        else:
            return Response("Unknown plan ID"), 400
    else:
        recurring = False
        amount = int(float(request.form['amount']) * 100)

    order = Order(request.form['name'], request.form['email'],
                  request.form.get('show', ''),
                  request.form.get('onair', 'n') == 'y',
                  request.form.get('firsttime', 'n') == 'y',
                  amount, recurring)

    if premiums != "no":
        order.set_premiums(premiums,
                           request.form.get('tshirtsize', None),
                           request.form.get('tshirtcolor', None),
                           request.form.get('sweatshirtsize', None))

    if premiums == "ship":
        # add shipping cost, if our order exceeds the minimum amount for
        # shipping cost (e.g., lowest tier has free shipping)
        if amount >= app.config['DONATE_SHIPPING_MINIMUM']:
            shipping_cost = int(app.config['DONATE_SHIPPING_COST']) * 100
            amount += int(app.config['DONATE_SHIPPING_COST']) * 100

        order.set_address(request.form['address_1'], request.form['address_2'],
                          request.form['city'], request.form['state'],
                          request.form['zipcode'])

    token = request.form['stripe_token']
    if len(token) <= 0:
        return Response("stripe_token was empty"), 400

    if recurring:
        if not process_stripe_recurring(order, token, plan, shipping_cost):
            return Response("Your card was declined. Please try again with "\
                            "a different method of payment."), 400
    else:
        if not process_stripe_onetime(order, token, amount):
            return Response("Your card was declined. Please try again with "\
                            "a different method of payment."), 400

    db.session.add(order)
    db.session.commit()

    return Response("Thanks for your order!")

@bp.route('/thanks')
def thanks():
    return render_template('donate/thanks.html')


@bp.route('/missioncontrol', methods=['GET', 'POST'])
@local_only
@auth.check_access('missioncontrol')
def missioncontrol_index():
    # TODO: add recurring donation support for mission control

    if 'amount' in request.form:
        premiums = request.form.get('premiums', 'no')
        amount = int(float(request.form['amount']) * 100)

        order = Order(request.form.get('name', ''),
                      request.form.get('email', ''),
                      request.form.get('show', ''),
                      request.form.get('onair', 'n') == 'y',
                      request.form.get('firsttime', 'n') == 'y',
                      amount, False)

        if premiums != "no":
            order.set_premiums(premiums,
                               request.form.get('tshirtsize', None),
                               request.form.get('tshirtcolor', None),
                               request.form.get('sweatshirtsize', None))

        if premiums == "ship":
            # add shipping cost, if our order exceeds the minimum amount for
            # shipping cost (e.g., lowest tier has free shipping)
            if amount >= app.config['DONATE_SHIPPING_MINIMUM']:
                amount += int(app.config['DONATE_SHIPPING_COST']) * 100

            order.set_address(request.form['address_1'], request.form['address_2'],
                              request.form['city'], request.form['state'],
                              request.form['zipcode'])

        if request.form['method'] == "stripe":
            if not process_stripe_onetime(order, request.form['stripe_token'],
                                          amount):
                return Response("Your card was declined. Please try again "\
                                "with a different method of payment."), 400

        db.session.add(order)
        db.session.commit()

        flash("The pledge was processed successfully.")


    return render_template('donate/missioncontrol/index.html')


@bp.route('/js/init.js')
def init_js():
    resp = make_response(render_template('donate/init.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp
