from flask import g
from flask_pymongo import PyMongo
from pymongo.errors import OperationFailure

from config import MONGO_URI


class MongoDBConnection:
    app = None
    def __init__(self, app=None):
        self.app = app
        self.connected = False
        self.last_error = None
        self.mongo = PyMongo(MongoDBConnection.app if MongoDBConnection.app is not None else None)
        if app is not None:
            self.init_app(app)

    def is_connected(self):
        return self.connected and self.last_error is None

    def init_app(self, app):
        app.config['MONGO_URI'] = MONGO_URI
        try:
            MongoDBConnection.app = app
            self.mongo.init_app(app)
            self.mongo.cx.server_info()
        except OperationFailure as e:
            self.last_error = e
           # raise e TODO: Custom error screens 1
        else:
            self.connected = True