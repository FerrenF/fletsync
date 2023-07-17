
from flask import Flask, g

from config import ETSY_OPENAPI_URL, WC_OPENAPI_URL

from util.openapi.etsy_openapi import EtsyOpenAPI
from util.openapi.wc_openapi import WooCommerceOpenAPI


def app_register_globals(app: Flask):
    from models.restClientManager import fletsync_client_manager
    with app.app_context():
        from util.authentication.userFunctions import init_login_manager
        from database.connection import mongo as db_connection
        from util.fl_session import init_session

        db_connection.init_app(app)
        init_session(app)
        init_login_manager(app)

        fletsync_client_manager.add_client('etsy', EtsyOpenAPI.from_remote_json(ETSY_OPENAPI_URL))
        fletsync_client_manager.add_client('wc', WooCommerceOpenAPI.from_remote_json(WC_OPENAPI_URL))
        fletsync_client_manager.register_app(app)


