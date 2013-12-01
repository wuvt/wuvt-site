from flask import abort, flash, jsonify, render_template, redirect, \
        request, url_for, Response
try:
    from flask.ext.login import login_required, login_user
except:
    from flaskext.login import login_required, login_user

from wuvt import app
from wuvt import db
from wuvt import lib
from wuvt import redirect_back

from wuvt.models import User
from wuvt.trackman.admin_views import *


@app.route('/admin')
@login_required
def admin_index():
    return render_template('admin/index.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if 'username' in request.form:
        user = User.query.filter(User.username == request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect_back('admin_index')
        else:
            return Response("bad username or password")
    return render_template('admin/login.html', next=request.values.get('next'))
