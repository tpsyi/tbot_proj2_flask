import functools
import config
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import SingletonThreadPool
from app_dir.database.tabledef import web_admin
from app_dir.database import db_util

# engine = create_engine(config.APP_DATABASE, echo=False, poolclass=SingletonThreadPool)
# local_session = db_util.Session()

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        if error is None:
            local_session = db_util.Session()
            try:
                local_session.add(web_admin(username=username, password=generate_password_hash(password), active=False, reg_date=func.now()))
                local_session.commit()
            except:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))
        flash(error)
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        local_session = db_util.Session()
        user = local_session.query(web_admin).filter(web_admin.username == username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('main_app'))
        flash(error)
    return render_template('auth/login.html')

@auth_bp.before_app_request
def load_logged_in_user():
    local_session = db_util.Session()
    if not local_session.query(web_admin).all():
        session.clear()
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        try:
            g.user = {"username": local_session.query(web_admin).filter(web_admin.id == user_id).first().username}
        except:
            session.clear()
            g.user = None

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main_app'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view