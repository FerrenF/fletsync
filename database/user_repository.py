import json
import typing

from config import MONGO_DB, APP_NAME
from .connection import mongo

class UserRepository:
    @staticmethod
    def get_user_by_id(user_id):
        db = mongo.mongo.cx[MONGO_DB]
        result = db[APP_NAME + '_users'].find_one({'user_id': user_id})
        return result

    @staticmethod
    def get_user_by_name(user_name: typing.AnyStr):
        db = mongo.mongo.cx[MONGO_DB]
        return db[APP_NAME+'_users'].find_one({'user_name': user_name})

    @staticmethod
    def save_user(user):
        db = mongo.mongo.cx[MONGO_DB]
        db[APP_NAME+'_users'].update_one({'user_id': user.user_id}, {'$set': user.to_dict()})

    @staticmethod
    def delete_user(user_id):
        db = mongo.mongo.cx[MONGO_DB]
        db[APP_NAME+'_users'].delete_one({'user_id': user_id})