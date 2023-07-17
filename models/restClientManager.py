class RESTClientManager:
    def __init__(self):
        self.clients = {}

    def add_client(self, platform, client):
        self.clients[platform] = client

    def remove_client(self, platform):
        if platform in self.clients:
            del self.clients[platform]

    def get_client(self, platform):
        return self.clients.get(platform)

    def get_all_clients(self):
        return self.clients.values()

    def is_authorized(self, platform):
        client = self.clients.get(platform)
        if client:
            return client.authorized()
        return False

    def register_app(self, app):
        for interface in self.clients.values():
            interface.register_app(app)


fletsync_client_manager = RESTClientManager()