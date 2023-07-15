from flask import Flask
from database.connection import mongo as db_connection
from views.index import index
from views.tests import tests_page
from util.fl_session import init_session
from config import APP_NAME
from controllers.user_auth import init_login_manager

from views.login import login
from views.logout import logout


app = Flask(APP_NAME)
app.config.from_pyfile('config.py')
db_connection.init_app(app)

init_session(app)
init_login_manager(app)

from util.openapi.etsyopenapi import etsy_api

etsy_api.register_app(app)




def load_routes():
    routes = {
        '/': ('index', index, ['GET']),
        '/login': ('login', login, ['POST', 'GET']),
        '/logout': ('logout', logout, ['POST', 'GET']),
        '/tests': ('tests', tests_page, ['POST', 'GET']),

    }

    for route, (endpoint, view_func, methods) in routes.items():
        app.add_url_rule(route, endpoint, view_func, methods=methods)



load_routes()

if __name__ == "main":
    app.run()




