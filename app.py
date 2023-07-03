from flask import Flask, render_template
from flask_login import current_user

import views.auth_etsy.login
from util.oauth import EtsyOAuthHandler
from views.auth_etsy.authorize import authorize
from views.index import index
from views.tests import tests_page
from util.fl_session import init_session, get_user_in_session
from config import APP_NAME, APP_URL
from controllers.user_auth import init_login_manager

from database.connection import mongo
from views.login import login
from views.logout import logout
from util.misc import meta_data

app = Flask(APP_NAME)
app.config.from_pyfile('config.py')
mongo.init_app(app)
init_session(app)
init_login_manager(app)

etsy_oauth = EtsyOAuthHandler(app)

def load_routes():
    routes = {
        '/': ('index', index, ['GET']),
        '/login': ('login', login, ['POST', 'GET']),
        '/logout': ('logout', logout, ['POST', 'GET']),
        '/tests': ('tests', tests_page, ['POST', 'GET']),

        '/etsy/authorize': ('etsy_authorize', views.auth_etsy.authorize.authorize, ['POST', 'GET']),
        '/etsy/login': ('etsy_login', views.auth_etsy.login.login, ['POST', 'GET']),
    }

    for route, (endpoint, view_func, methods) in routes.items():
        app.add_url_rule(route, endpoint, view_func, methods=methods)


load_routes()

if __name__ == '__main__':
    app.run()


