from datetime import datetime, timedelta

from authlib.common.urls import quote
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from flask import Flask, url_for, request, redirect

from config import APP_NAME
from models.AuthorizationFlowInstance import AuthorizationFlowInstance
from util.openapi.authorization.auth_type import AuthType
from util.openapi.openapi_interface import PreparedOpenAPICommand


class OAuthHandler(AuthType):

    def __init__(self, app: Flask=None, name="authorization", user_id=None, requested_scope=None, request_parameters=None):
        """

        :param app: We need this because we have to register routes for the authorization flow.
        :param name: It's best to set this to something identifiable.
        :param user_id: The user id is required to uniquely associate authorization requests to particular users.
        :param requested_scope: This is the child class's problem
        """
        super().__init__(type(self))
        self.name = name
        self.requested_scope = requested_scope

        self.auth_instance = AuthorizationFlowInstance(name)
        self.auth_instance.scope = self.requested_scope
        self.auth_instance.authorization_type = 'initial'

        self.associated_user = user_id
        self.oauth_session = OAuth2Session()
        self.oauth_uris = {
            'tokenUrl': None,
            'authorizationUrl': None
        }
        self.oauth_session.client_id = request_parameters.get('client_id',APP_NAME)
        self.request_parameters = {}
        self.registered_app = app

        # Off to register routes we go
        if app:
            self.register_app(app)

    ### Required methods for AuthType

    @property
    def authorized(self):
        if self.auth_instance.has_valid_token():
            return True
        if self.auth_instance.is_expired():
            if self.auth_instance.authorization_type == 'initial':
                AuthorizationFlowInstance.purge_request(self.auth_instance)
            # TODO: Request refresh token because the authorization type is probably 'refresh'
        return False

    def wrap_command(self, command : PreparedOpenAPICommand):
        return command

    @property
    def app_registered(self):
        return self.registered_app is not None

    def register_app(self, app):
        routes = {
            f'/{self.name}/authorize': (f'{self.name}_authorize', self.oauth_authorize, ['POST', 'GET']),
            f'/{self.name}/login': (f'{self.name}_login', self.oauth_login, ['POST', 'GET']),
            f'/{self.name}/purge': (f'{self.name}_purge_authorization', self.oauth_purge_authorization, ['GET'])
        }

        for route, (endpoint, view_func, methods) in routes.items():
            app.add_url_rule(route, endpoint, view_func, methods=methods)

    def associate_user(self, user_id):
        self.associated_user = user_id
        if self.auth_instance is not None:
            self.auth_instance.user_id = user_id

    def retrieve_saved_authorization(self):
        instance = AuthorizationFlowInstance.retrieve_request_by(self.name, self.associated_user)
        if instance is not None:
            self.auth_instance = instance
    ### End required methods for AuthType



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
        # TODO: This looks like a pretty good place to check if a token is expired or not
        return self.auth_instance.authorization_token

    def create_authorization_endpoint(self):

        code_challenge = create_s256_code_challenge(self.auth_instance.code_verifier)
        redirect_uri = url_for(f'{self.name}_authorize', _external=True, _scheme='https')
        additional_params = {
            'redirect_uri': redirect_uri,
            'code_challenge_method': 'S256',
            'code_challenge': code_challenge,
            'code_verifier': self.auth_instance.code_verifier,
            'scope': str(self.requested_scope)}
        additional_params.update(self.request_parameters)
        uri, state = self.oauth_session.create_authorization_url(self.oauth_uris['authorizationUrl'],
                                                                 **additional_params)

        self.auth_instance.authorization_state = state
        self.update_request_instance()
        return uri



    def fetch_token(self):

        if self.auth_instance is None:
            self.retrieve_saved_authorization()
        if self.auth_instance is None:
            self.auth_instance = AuthorizationFlowInstance('name', error="No authorization instance saved")
        else:
            target_instance = self.auth_instance
            redirect_uri = url_for(f'{self.name}_authorize', _external=True, _scheme='https')
            additional_params = {
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri,
                'code_verifier': quote(target_instance.code_verifier),
                'code': quote(target_instance.authorization_code)
            }

            token = self.oauth_session.fetch_token(self.oauth_uris['tokenUrl'], **additional_params)

            target_instance.set_authorize(token['access_token'], token['refresh_token'],
                                          (datetime.now() + timedelta(seconds=token['expires_in'])))
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
                AuthorizationFlowInstance.purge_request(target_instance)
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

            print('successful authorization flow')
            self.auth_instance = target_instance
            self.update_request_instance(target_instance)
        else:
            print(request.args)

        if res:
            if not self.fetch_token():
                res = False
        return error() if not res else success()

    def purge_request_instance(self):
        deletion = AuthorizationFlowInstance.purge_request(self.auth_instance)
        self.auth_instance = AuthorizationFlowInstance(self.name)
        return deletion

    def update_request_instance(self, store_request=None):
        if self.associated_user is None or self.name is None:
            return

        if store_request:
            store_request.store()
            return
        self.auth_instance.store()


    # URL Targets

    def oauth_authorize(self):
        from flask_login import current_user
        if current_user.is_authenticated:
            self.retrieve_saved_authorization()
            self.receive_authorization_and_fetch(self.redirect_on_success, self.redirect_on_failure)
        return redirect(url_for('index'))

    def oauth_purge_authorization(self):
        from flask_login import current_user
        if current_user.is_authenticated:
            self.associate_user(current_user.get_id())
            self.retrieve_saved_authorization()
            self.purge_request_instance()
        return redirect(url_for('index'))

    def oauth_login(self):
        from flask_login import current_user
        if current_user.is_authenticated:
            self.associate_user(current_user.get_id())
            self.retrieve_saved_authorization()
            destination = self.create_authorization_endpoint()
        else:
            destination = url_for('index')
        return redirect(destination)

    def redirect_on_success(self):
        return redirect(url_for('index'))

    def redirect_on_failure(self, error):
        return redirect(url_for('index'))
