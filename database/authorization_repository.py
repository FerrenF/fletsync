from config import MONGO_DB, APP_NAME
from .connection import mongo


class AuthorizationRepository:

    collection_name = APP_NAME + '_authorizations'

    @staticmethod
    def get_authorization_from_user_id(user_id, name):
        db = mongo.mongo.cx[MONGO_DB]
        result = db[AuthorizationRepository.collection_name].find_one({'user_id': user_id, 'name': name})
        return result

    @staticmethod
    def store_authorization(auth):
        db = mongo.mongo.cx[MONGO_DB]
        result = db[AuthorizationRepository.collection_name].update_one({'user_id': auth.user_id},
                                                               {'$set': auth.to_dict()}, upsert=True)
        return result.modified_count

    @staticmethod
    def delete_authorization_for_user_id(user_id, name):
        db = mongo.mongo.cx[MONGO_DB]
        result = db[AuthorizationRepository.collection_name].delete_many({'user_id': user_id, 'name': name})
        return result.deleted_count
