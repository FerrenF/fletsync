import random
import string

import bson
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from models.user import User
from database.connection import initialize_db, mongo, initialize_db_from_uri
from config import MONGO_DB, MONGO_URI, ADMIN_USERNAME, APP_NAME
from util.crypt import fl_hash_password


def create_collections(db):
    print("Creating collections...")
    users_collection = db[APP_NAME+"_users"]
    p_gen = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    print(fl_hash_password(p_gen))
    user = {
        'user_id': bson.ObjectId().__str__(),
        'user_name': ADMIN_USERNAME,
        'password_hash': fl_hash_password(p_gen),
        'role': 'admin'
    }
    result = users_collection.replace_one({'user_name': ADMIN_USERNAME}, user, upsert=True)
    if result.modified_count:
        print(f"Admin user written or OVERWRITTEN in database: PASSWORD: '{p_gen}'")
    else:
        print("problem writing admin account.")



def error_function(e):
    print("Error encountered: "+str(e))


def initialize_database():

    app = initialize_db_from_uri(MONGO_URI, database=MONGO_DB, error=error_function)

    if app is not False and mongo.mongo is not None:
        if MONGO_DB not in mongo.mongo.cx.list_database_names():
            mongo.cx.get_database(MONGO_DB)
            print(f"Created database '{MONGO_DB}'")
        db = mongo.mongo.cx[MONGO_DB]
        create_collections(db)
    return app


print("Running setup script...")
app = initialize_database()


from database.user_repository import UserRepository

def test_database():

    error = False
    print("Looking for collections...")

    user_collection = APP_NAME+'_users'
    require_collections = [user_collection]
    current_collections = mongo.mongo.cx[MONGO_DB].list_collection_names()
    for coll in require_collections:
        if coll not in current_collections:
            print("Missing collection: "+coll)

    print("Confirming presence of admin account...")
    admin_user = User.get_by_name(ADMIN_USERNAME)
    if admin_user is None:
        print("Warning: Admin user is not detected...")
    else:
        print("Admin user present")

    if not error:
        print("Everything accounted for so far...")


print("Testing...")
test_database()

del app