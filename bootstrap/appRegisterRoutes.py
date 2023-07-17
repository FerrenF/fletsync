from flask import Flask

from controllers.indexController import index
from controllers.testsController import tests_page
from controllers.loginController import login, logout


def app_register_routes(app: Flask):
    routes = {
        '/': ('index', index, ['GET']),
        '/login': ('login', login, ['POST', 'GET']),
        '/logout': ('logout', logout, ['POST', 'GET']),
        '/tests': ('tests', tests_page, ['POST', 'GET']),

    }

    for route, (endpoint, view_func, methods) in routes.items():
        app.add_url_rule(route, endpoint, view_func, methods=methods)

