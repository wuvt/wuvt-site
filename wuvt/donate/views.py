import datetime
from flask import flash, make_response, redirect, render_template, request, \
        url_for, Response
from wuvt import app
from wuvt import db
from wuvt.donate import bp
from wuvt.donate import get_plan, list_plans, mail, process_stripe_onetime, \
        process_stripe_recurring
from wuvt.donate.models import Order
from wuvt.donate.view_utils import load_premiums_config
from wuvt.view_utils import local_only


@bp.route('/onetime')
def donate_onetime():
    return render_template('donate/premium_form.html', active_flow='donate',
                           premiums_config=load_premiums_config())


@bp.route('/monthly')
def donate_recurring():
    return render_template('donate/recurring_form.html', plans=list_plans(),
                           active_flow='donate',
                           premiums_config=load_premiums_config())


def process_order(method):
    premiums_config = load_premiums_config()
    plan_id = request.form.get('plan', '')
    shipping_cost = 0

    if len(plan_id) > 0:
        recurring = True
        plan = get_plan(plan_id)

        if plan:
            amount = plan.amount
        else:
            return False, "Unknown plan ID"
    else:
        recurring = False
        amount_entry = request.form.get('amount', '').strip().lstrip('$')
        if len(amount_entry) <= 0:
            return False, "Please enter an amount to donate"

        amount = int(float(amount_entry) * 100)
        if amount <= 0:
            return False, "Amount must be greater than 0"

    order = Order(request.form.get('name', '').strip(),
                  request.form.get('email', '').strip(),
                  request.form.get('show', '').strip(),
                  request.form.get('onair', 'n') == 'y',
                  request.form.get('firsttime', 'n') == 'y',
                  amount, recurring)
    order.remote_addr = request.remote_addr
    order.set_user_agent(request.user_agent)

    if 'phone' in request.form:
        # Removes anything non-numeric from the phone string, so that we
        # no longer have exceptions when Mission Control users use something
        # like (540) 555-5555 instead of 540-555-5555 or 5405555555.
        order.phone = ''.join([char for char in request.form['phone'] if char
                               in "0123456789"])

    if 'comment' in request.form:
        order.donor_comment = request.form['comment'].strip()

    if premiums_config['enabled']:
        premiums = request.form.get('premiums', 'no')

        if premiums != "no":
            # TODO: check that these are valid
            order.set_premiums(premiums,
                               request.form.get('tshirtsize', None),
                               request.form.get('tshirtcolor', None),
                               request.form.get('sweatshirtsize', None))

        if premiums == "ship":
            # add shipping cost, if our order exceeds the minimum amount for
            # shipping cost (e.g., lowest tier has free shipping)
            if amount >= premiums_config['shipping_minimum']:
                shipping_cost = premiums_config['shipping_cost']

            order.set_address(request.form['address_1'],
                              request.form['address_2'],
                              request.form['city'],
                              request.form['state'],
                              request.form['zipcode'])

    db.session.add(order)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise

    if method == 'stripe' or method == 'stripe_missioncontrol':
        token = request.form['stripe_token']
        if len(token) <= 0:
            return False, "stripe_token was empty"

        if recurring:
            if process_stripe_recurring(order, token, plan, shipping_cost):
                order.set_paid(method)
                mail.send_receipt(order)
            else:
                return False, "Your card was declined. Please try again with "\
                        "a different method of payment."
        else:
            if process_stripe_onetime(order, token, amount + shipping_cost):
                order.set_paid(method)
                mail.send_receipt(order)
            else:
                return False, "Your card was declined. Please try again with "\
                        "a different method of payment."
    else:
        if recurring:
            return False, "Only Stripe is supported for recurring payments."
        elif method != 'later':
            order.set_paid(method)

    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise

    return True, "Thanks for your order!"


@bp.route('/process', methods=['POST'])
def process():
    errors = []
    premiums = request.form.get('premiums', 'no')
    if premiums != "no" and len(request.form['name']) <= 0:
        errors.append("Please enter your name")

    if premiums == "ship":
        # verify we included address information

        if len(request.form['address_1']) <= 0:
            errors.append("Please enter an address line 1")

        if len(request.form['city']) <= 0:
            errors.append("Please enter a city")

        if len(request.form['state']) <= 0:
            errors.append("Please enter a state")

        if len(request.form['zipcode']) <= 0:
            errors.append("Please enter a a ZIP code")

    if len(errors) > 0:
        return render_template('donate/error.html', messages=errors), 400

    success, msg = process_order('stripe')
    if success:
        return Response(msg)
    else:
        return render_template('donate/error.html', messages=[msg]), 400


@bp.route('/thanks')
def thanks():
    return render_template('donate/thanks.html')


@bp.route('/missioncontrol')
@local_only
def missioncontrol_index():
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=12)
    orders = Order.query.\
        filter(Order.placed_date > cutoff).\
        order_by(db.desc(Order.id)).limit(app.config['ARTISTS_PER_PAGE'])
    return render_template('donate/missioncontrol/index.html',
                           plans=list_plans(), orders=orders,
                           premiums_config=load_premiums_config())


@bp.route('/missioncontrol/process', methods=['POST'])
@local_only
def missioncontrol_process():
    success, msg = process_order(request.form['method'])
    if success:
        flash("The pledge was processed successfully.")
        return redirect(url_for('.missioncontrol_index'))
    else:
        return Response(msg), 400


@bp.route('/js/init.js')
def init_js():
    resp = make_response(render_template(
        'donate/init.js',
        premiums_config=load_premiums_config()))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@bp.route('/missioncontrol/js/donate_init.js')
@local_only
def missioncontrol_donate_js():
    resp = make_response(render_template(
        'donate/missioncontrol/donate.js',
        premiums_config=load_premiums_config()))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp
