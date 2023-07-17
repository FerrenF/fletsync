from flask import Flask

from config import ETSY_API_KEY
from util.openapi.authorization.etsy_oauth_scopes import EtsyOAuthScope
from util.openapi.authorization.oauth2_auth_handler import OAuthHandler
from util.openapi.openapi_interface import PreparedOpenAPICommand


class EtsyOAuthHandler(OAuthHandler):

    def __init__(self, app: Flask = None, user_id = None):

        requested_scope = EtsyOAuthScope()
        requested_scope['profile_r'] = True
        requested_scope['shops_r'] = True
        requested_scope['shops_w'] = True
        requested_scope['listings_r'] = True
        requested_scope['listings_w'] = True
        requested_scope['listings_d'] = True
        request_parameters = {
            'client_id': ETSY_API_KEY
        }

        super().__init__(app, 'etsy', user_id, requested_scope, request_parameters)
        # These permissions are requried by fletsync

        self.oauth_uris = {
            'tokenUrl': 'https://api.etsy.com/v3/public/oauth/token',
            'authorizationUrl': 'https://www.etsy.com/oauth/connect'
        }

    def wrap_command(self, command: PreparedOpenAPICommand):
        command.headers.update({'Authorization': 'Bearer '+self.auth_instance.authorization_token})
        return command

    def get_token_id_prefix(self):
        if self.authorized:
            str_t = str(self.auth_instance.authorization_token)
            dot_ind = str_t.find('.')
            return str_t[0:dot_ind] if dot_ind != -1 else None



