from flask import g
from flask_pymongo import PyMongo
from pymongo.errors import OperationFailure

from config import MONGO_URI


class MongoDBConnection:
    def __init__(self, app=None):
        self.app = app
        self.connected = False
        self.last_error = None
        if app is not None:
            self.init_app(app)

    def is_connected(self):
        return self.connected or self.last_error

    def init_app(self, app):
        app.config['MONGO_URI'] = MONGO_URI
        try:
            self.mongo = PyMongo(app)
            self.mongo.cx.server_info()
        except OperationFailure as e:
            self.last_error = e
           # raise e TODO: Custom error screens 1
        else:
            self.connected = True