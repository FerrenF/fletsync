import requests
from flask import Flask
from flask_login import current_user

from config import ETSY_OPENAPI_URL

from util.openapi.oauth.etsy_oauth_handler import EtsyOAuthHandler
from views.oauth import etsy_command
from util.openapi.openapi_interface import OpenAPI_Interface


from views.oauth.etsy_authorize import etsy_authorize, etsy_purge_authorization
from views.oauth.etsy_login import etsy_login


#Things this class needs to succeed: built-in oauth management and a way to link user ID for initial requests


class Etsy_OpenAPI(OpenAPI_Interface):
    def __init__(self, version, servers, commands, schemas, security):
        super().__init__(version, servers, commands, schemas, security)
        self.request_session = None
        self.oauth_session = EtsyOAuthHandler(None)
        self.stored_parameters = dict()
        self.initialize_request_session()
        self.registered_app = None

        if security.get('oauth2', None) is not None:

            oauth_security = security['oauth2']
            flows = oauth_security['flows']
            uris = flows.get('authorizationCode', None)
            if uris is not None:
                self.oauth_session.set_oauth_uris(uris['tokenUrl'],uris['authorizationUrl'])


    # We are going to cheat and not make an API call here.
    def get_user_id(self):
        return self.oauth_session.get_token_id_prefix()

    def getMe(self):
        command = self.make_command('getMe')
        print(command)
        response = self.send_command(command)
        print(response)

    @property
    def app_registered(self):
        return self.registered_app is not None

    def register_app(self, app: Flask):
        if app is None:
            return

        routes = {
            '/etsy/authorize': ('etsy_authorize', etsy_authorize, ['POST', 'GET']),
            '/etsy/login': ('etsy_login', etsy_login, ['POST', 'GET']),
            '/etsy/command': ('etsy_command', etsy_command, ['POST', 'GET']),
            '/etsy/purge': ('etsy_purge_authorization', etsy_purge_authorization, ['GET'])
        }

        for route, (endpoint, view_func, methods) in routes.items():
            app.add_url_rule(route, endpoint, view_func, methods=methods)

        #self.registered_app = app
    def retrieve_saved_authorization(self):
        if self.oauth_session is not None:
            self.oauth_session.retrieve_saved_authorization()

    def initialize_request_session(self):
        self.request_session = requests.Session()

    @staticmethod
    def from_remote_json(uri):
        o_api = OpenAPI_Interface.from_remote_json(uri)
        return Etsy_OpenAPI(o_api.version,
                            o_api.servers,
                            o_api.command_dictionary,
                            o_api.schema_dictionary,
                            o_api.security_dictionary)


etsy_api = Etsy_OpenAPI.from_remote_json(ETSY_OPENAPI_URL)