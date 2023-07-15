import datetime
from config import MONGO_DB, APP_NAME
from models.uriCacheEntry import UriCacheEntry


class UriCache:
    collection_name = APP_NAME + '_uri_cache'

    @staticmethod
    def store_uri(uri, data):
        from .connection import mongo as f_mongo
        entry = UriCacheEntry(uri, data)
        db = f_mongo.mongo.cx[MONGO_DB]

        db[UriCache.collection_name].update_one({'uri': uri}, {'$set': entry.__dict__}, upsert=True)

    @staticmethod
    def get_if_fresh(uri, what_does_fresh_mean=datetime.timedelta(), purge_if_stale=True):
        from .connection import mongo as f_mongo
        db = f_mongo.mongo.cx[MONGO_DB]
        entry = db[UriCache.collection_name].find_one({'uri': uri})
        if entry:
            last_cache = entry.get('last_cache')
            if last_cache:
                current_time = datetime.datetime.now()
                time_difference = current_time - last_cache
                if time_difference <= what_does_fresh_mean:
                    print("retrieved from cache: " + uri)
                    return entry['data']
                elif purge_if_stale:
                    UriCache.purge_cache(uri)
        return None

    @staticmethod
    def purge_cache(uri=None):
        from .connection import mongo
        db = mongo.mongo.cx[MONGO_DB]
        if uri:
            db[UriCache.collection_name].delete_many({'uri': uri})
        else:
            db[UriCache.collection_name].delete_many({})