import requests
from flask import Flask

from util.openapi.authorization.wc_auth_handler import WooCommerceAuthHandler
from util.openapi.openapi_interface import OpenAPI_Interface, OpenAPI_CommandException


class WooCommerceOpenAPI(OpenAPI_Interface):
    def __init__(self, version, servers, commands, schemas, security, app: Flask = None):
        super().__init__(version, servers, commands, schemas, security, app)
        self.request_session = None
        self.stored_parameters = dict()
        self.initialize_request_session()

        authtype = WooCommerceAuthHandler(app)
        self.add_auth_type(authtype)

    # We are going to cheat and not make an API call here. If we are authorized then we naturally have the user ID.
    def get_user_id(self):
        if self.authorized:
            return None
        else:
            return None

    def getProducts(self, **kwargs):
        try:
            command = self.make_command('getProducts', **kwargs)
        except OpenAPI_CommandException as E:
            print(f'{E.type}:{E.description}')
            return None

        result = self.send_command(command)
        return result

    def initialize_request_session(self):
        self.request_session = requests.Session()

    @staticmethod
    def from_remote_json(uri, app : Flask = None):
        o_api = OpenAPI_Interface.from_remote_json(uri)
        print("Registered api at "+ uri + " with "+ (str(len(o_api.command_dictionary.keys()))) + " commands")
        return WooCommerceOpenAPI(o_api.version,
                           o_api.servers,
                           o_api.command_dictionary,
                           o_api.schema_dictionary,
                           o_api.security_dictionary, app)
