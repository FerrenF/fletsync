import requests
from flask import Flask

from config import ETSY_OPENAPI_URL, ETSY_API_KEY

from util.openapi.oauth.etsy_oauth_handler import EtsyOAuthHandler, ApiKeyHandler
from util.openapi.openapi_interface import OpenAPI_Interface


class EtsyOpenAPI(OpenAPI_Interface):
    def __init__(self, version, servers, commands, schemas, security, app: Flask = None):
        super().__init__(version, servers, commands, schemas, security, app)
        self.request_session = None
        self.stored_parameters = dict()
        self.initialize_request_session()


        # Specific to etsy's OpenAPI documentation. The same functionality will need to be added
        oauth_security = security['oauth2']
        flows = oauth_security['flows']
        uris = flows.get('authorizationCode', None)
        if uris is not None:

            oauth2type = EtsyOAuthHandler(app)
            oauth2type.set_oauth_uris(uris['tokenUrl'], uris['authorizationUrl'])
            self.add_auth_type(oauth2type)

        self.add_auth_type(ApiKeyHandler(ETSY_API_KEY))

    # We are going to cheat and not make an API call here. If we are authorized then we naturally have the user ID.
    def get_user_id(self):
        if self.authorized:
            t = type(EtsyOAuthHandler())
            auth = self.get_auth_type(t)
            return auth.get_token_id_prefix() if auth is not None else None
        else:
            return None


    def getMe(self):
        command = self.make_command('getMe')
        result = self.send_command(command)
        print(result.content)
        return result


    def initialize_request_session(self):
        self.request_session = requests.Session()

    @staticmethod
    def from_remote_json(uri, app : Flask = None):
        o_api = OpenAPI_Interface.from_remote_json(uri)
        return EtsyOpenAPI(o_api.version,
                           o_api.servers,
                           o_api.command_dictionary,
                           o_api.schema_dictionary,
                           o_api.security_dictionary, app)


etsy_api = EtsyOpenAPI.from_remote_json(ETSY_OPENAPI_URL)
