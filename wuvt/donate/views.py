import datetime
from flask import flash, make_response, redirect, render_template, request, \
        url_for, Response
from wuvt import app
from wuvt import db
from wuvt.donate import bp
from wuvt.donate import get_plan, list_plans, mail, process_stripe_onetime, \
        process_stripe_recurring
from wuvt.donate.models import Order
from wuvt.view_utils import local_only


@bp.route('/onetime')
def donate_onetime():
    return render_template('donate/premium_form.html', active_flow='donate')


@bp.route('/monthly')
def donate_recurring():
    return render_template('donate/recurring_form.html', plans=list_plans(),
                           active_flow='donate')


def process_order(method):
    premiums = request.form.get('premiums', 'no')
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

    if 'phone' in request.form:
        # if a phone number is provided, set it
        order.phone = request.form['phone'].strip()

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

        order.set_address(request.form['address_1'], request.form['address_2'],
                          request.form['city'], request.form['state'],
                          request.form['zipcode'])

    if method == u'stripe':
        token = request.form['stripe_token']
        if len(token) <= 0:
            return False, "stripe_token was empty"

        if recurring:
            if process_stripe_recurring(order, token, plan, shipping_cost):
                order.set_paid(u'stripe')
                mail.send_receipt(order)
            else:
                return False, "Your card was declined. Please try again with "\
                        "a different method of payment."
        else:
            if process_stripe_onetime(order, token, amount + shipping_cost):
                order.set_paid(u'stripe')
                mail.send_receipt(order)
            else:
                return False, "Your card was declined. Please try again with "\
                        "a different method of payment."
    else:
        if recurring:
            return False, "Only Stripe is supported for recurring payments."
        elif method != u'later':
            order.set_paid(method)

    db.session.add(order)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise
    return True, "Thanks for your order!"


@bp.route('/process', methods=['POST'])
def process():
    errors = []
    if request.form['premiums'] != "no" and len(request.form['name']) <= 0:
        errors.append("Please enter your name")

    if request.form['premiums'] == "ship":
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

    success, msg = process_order(u'stripe')
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
                           plans=list_plans(), orders=orders)


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
    resp = make_response(render_template('donate/init.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp


@bp.route('/missioncontrol/js/donate_init.js')
@local_only
def missioncontrol_donate_js():
    resp = make_response(render_template(
        'donate/missioncontrol/donate.js'))
    resp.headers['Content-Type'] = "application/javascript; charset=utf-8"
    return resp
