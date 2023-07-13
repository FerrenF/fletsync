import datetime


class UriCacheEntry:
    def __init__(self, uri, data):
        self.last_cache = datetime.datetime.now()
        self.data = data
        self.uri = uri
