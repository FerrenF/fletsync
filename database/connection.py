from typing import Callable
from urllib.parse import quote_plus

import flask
from pymongo.errors import OperationFailure

from config import MONGO_URI, MONGO_DB, APP_NAME
from database.mongodb import MongoDBConnection
from util.uri import insert_db_into_uri


mongo = MongoDBConnection()

def initialize_db(app, error: Callable = None):
    app.config['MONGO_URI'] = MONGO_URI
    app.config['MONGO_DATABASE'] = MONGO_DB
    try:
        mongo.init_app(app)

    except OperationFailure as e:
        if error:
            error(e)
        return False
    # raise e TODO: Custom error screens 1
    return True


def initialize_db_from_uri(uri, database=None, error: Callable = None):

    app = flask.Flask(APP_NAME)
    app.config['MONGO_URI'] = MONGO_URI

    if database is not None:
        encoded_db_name = quote_plus(database)
        app.config['MONGO_DATABASE'] = insert_db_into_uri(uri, encoded_db_name)
    try:
        mongo.init_app(app)
    except OperationFailure as e:
        if error:
            error(e)
        return False
    # raise e TODO: Custom error screens 1
    return app


