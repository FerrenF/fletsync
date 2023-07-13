from datetime import datetime, timedelta

from authlib.common.urls import quote
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from flask import url_for, request

from config import ETSY_API_KEY
from models.auth import AuthorizationInstance
from util.openapi.oauth.etsy_oauth_scopes import EtsyOAuthScope


class EtsyOAuthHandler:

    def __init__(self, user_id= None):

        # These permissions are requried by fletsync
        self.required_scope = EtsyOAuthScope()
        self.required_scope['profile_r'] = True
        self.required_scope['shops_r'] = True
        self.required_scope['shops_w'] = True
        self.required_scope['listings_r'] = True
        self.required_scope['listings_w'] = True
        self.required_scope['listings_d'] = True

        self.auth_instance = AuthorizationInstance('etsy')
        self.auth_instance.scope = self.required_scope
        self.auth_instance.authorization_type = 'initial'

        self.associated_user = user_id
        self.oauth_uris = {
            'tokenUrl': 'https://api.etsy.com/v3/public/oauth/token',
            'authorizationUrl': 'https://www.etsy.com/oauth/connect'
        }
        self.request_parameters = {
            'client_id': ETSY_API_KEY
        }

        self.oauth_session = OAuth2Session(**self.request_parameters)

    def get_authorization_header(self):
        return {'Authorization': 'Bearer '+self.auth_instance.authorization_token}

    def get_token_id_prefix(self):
        if self.authorized:
            str_t = str(self.auth_instance.authorization_token)
            dot_ind = str_t.find('.')
            return str_t[0:dot_ind] if dot_ind != -1 else None

    def associate_user(self, user_id):
        self.associated_user = user_id
        if self.auth_instance is not None:
            self.auth_instance.user_id = user_id

    def set_oauth_uris(self, tokenUrl, authorizationUrl):
        self.oauth_uris['tokenUrl'] = tokenUrl
        self.oauth_uris['authorizationUrl'] = authorizationUrl

    def get_authorized_token_scope(self):
        if not self.authorized:
            return None
        return self.auth_instance.scope

    def get_token(self):
        if not self.authorized:
            return None
        #TODO: This looks like a pretty good place to check if a token is expired or not
        return self.auth_instance.authorization_token

    @property
    def authorized(self):
        if self.auth_instance.has_valid_token():
            return True
        if self.auth_instance.is_expired():
            if self.auth_instance.authorization_type == 'initial':
                AuthorizationInstance.purge_request(self.auth_instance)
            #TODO: Request refresh token because the authorization type is probably 'refresh'
        return False

    def create_authorization_endpoint(self):

        target_instance = self.auth_instance
        code_challenge = create_s256_code_challenge(self.auth_instance.code_verifier)
        redirect_uri = url_for('etsy_authorize', _external=True, _scheme='https')
        additional_params = {
            'redirect_uri': redirect_uri,
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge,
            'code_verifier': self.auth_instance.code_verifier,
            'scope': str(self.required_scope)}

        uri, state = self.oauth_session.create_authorization_url(self.oauth_uris['authorizationUrl'], **additional_params)

        self.auth_instance.authorization_state = state
        self.update_request_instance()
        return uri

    def retrieve_saved_authorization(self):
        instance = AuthorizationInstance.retrieve_request_by('etsy', self.associated_user)
        if instance is not None:
            self.auth_instance = instance

    def fetch_token(self):

        if self.auth_instance is None:
            self.retrieve_saved_authorization()
        if self.auth_instance is None:
            self.auth_instance = AuthorizationInstance('name', error="No authorization instance saved")
        else:
            target_instance = self.auth_instance
            redirect_uri = url_for('etsy_authorize', _external=True, _scheme='https')
            additional_params = {
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri,
                'code_verifier': quote(target_instance.code_verifier),
                'code': quote(target_instance.authorization_code),
                'client_id': quote(self.request_parameters['client_id'])
            }

            token = self.oauth_session.fetch_token(self.oauth_uris['tokenUrl'], **additional_params)

            target_instance.set_authorize(token['access_token'], token['refresh_token'],
                                          (datetime.now()+timedelta(seconds=token['expires_in'])).strftime(AuthorizationInstance.DATE_FORMAT))
            self.auth_instance = target_instance
            self.update_request_instance(target_instance)
            return token
        return None

    def receive_authorization_and_fetch(self, success, error):

        if self.auth_instance is None:
            self.retrieve_saved_authorization()
        res = False
        target_instance = self.auth_instance

        if request is None:
            return error("Not in context.")

        if request.method == 'GET':
            req = request.args
            req_state = req.get('state', None)

            if target_instance.authorization_state != req_state:
                AuthorizationInstance.purge_request(target_instance)
                return error("Request state did not match.")

            if 'error' not in req:
                # Successful authorization
                req_code = req.get('code', None)

                if req_code is None:
                    # Malformed
                    return error("Malformed response - Code missing.")

                target_instance.authorization_code = req_code
                res = True
            else:
                # Authorization error
                target_instance.error = req.get('error')

            self.auth_instance = target_instance
            self.update_request_instance(target_instance)
        else:
            print(request.args)

        if res:
            if not self.fetch_token():
                res = False
        return error() if not res else success()

    def purge_request_instance(self):
        #if self.associated_user is None or self.auth_instance.user_id is None:
         #   return

        AuthorizationInstance.purge_request(self.auth_instance)
        self.auth_instance = AuthorizationInstance('etsy')
        return True
    def update_request_instance(self, store_request=None):

        if self.associated_user is None or self.auth_instance.user_id is None:
            return

        if store_request:
            store_request.store()
            return
        self.auth_instance.store()

