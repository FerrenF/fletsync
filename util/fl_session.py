
from flask import session
from flask_session import Session

from config import APP_NAME, SECRET_KEY

sess = Session()


def init_session(app):
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = SECRET_KEY
    app.secret_key = SECRET_KEY
    sess.init_app(app)
    return sess


def store_user_in_session(user):
    session[APP_NAME+'_user'] = user


def get_user_in_session():
    return session.get(APP_NAME+'_user')



