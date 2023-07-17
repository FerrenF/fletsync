import datetime
from dataclasses import dataclass

import requests
from flask import Flask, url_for, request, redirect

from config import APP_NAME, WC_API_AUTH_URL
from models.AuthorizationFlowInstance import AuthorizationFlowInstance
from util.openapi.authorization.auth_type import AuthType
from util.openapi.openapi_interface import PreparedOpenAPICommand


# WooCommerce REST API does NOT follow OAuth 2.0 Standards, therefore may I present WooCommerceAuthHandler class.
# ... It's ALMOST Oauth.

# With that being said, we will be storing it in the same place as authorization instances for actual Oauth2 Instances,
# as provided by our lovely db.

@dataclass
class WooCommerceAuthScope:
    read: bool = False
    write: bool = False

    def __str__(self):
        return "read_write" if self.read and self.write else \
            ("read" if self.read else ("write" if self.write else None))
class WooCommerceAuthHandler(AuthType):

    def __init__(self, app: Flask = None, user_id=None, requested_scope=WooCommerceAuthScope(True, True)):
        super().__init__(type(self))
        self.name = 'wc'
        self.auth_instance = None
        self.requested_scope = requested_scope

        self.auth_instance = AuthorizationFlowInstance(self.name)
        self.auth_instance.scope = self.requested_scope.__str__()
        self.auth_instance.authorization_type = 'permanent'

        self.associated_user = user_id

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
        return False

    def wrap_command(self, command : PreparedOpenAPICommand):
        command.arguments.update({
            'consumer_key': self.auth_instance.authorization_code,
            'consumer_secret': self.auth_instance.authorization_token
        })
        return command

    @property
    def app_registered(self):
        return self.registered_app is not None

    def register_app(self, app):
        routes = {
            f'/{self.name}/login': (f'{self.name}_login', self.auth_login, ['POST', 'GET']),
            f'/{self.name}/authorize': (f'{self.name}_authorize', self.auth_authorize, ['POST', 'GET']),
            f'/{self.name}/receive': (f'{self.name}_receive', self.auth_receive, ['POST']),
            f'/{self.name}/purge': (f'{self.name}_purge_authorization', self.auth_purge, ['GET'])
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

### End required methods

    def create_authorization_endpoint(self):

        builder = requests.Request(method='GET')
        builder.url = WC_API_AUTH_URL

        redirect_uri = url_for(f'{self.name}_authorize', _external=True, _scheme='https')
        callback_uri = url_for(f'{self.name}_receive', _external=True, _scheme='https')
        builder.params = {
            'return_url': redirect_uri,
            'app_name': APP_NAME,
            'callback_url': callback_uri,
            'user_id': self.associated_user,
            'scope': self.requested_scope.__str__()}

        prepared_builder = builder.prepare()
        uri = prepared_builder.url

        self.update_request_instance()
        return uri

    def receive_authorization(self, success, error):

        res = False
        target_instance = self.auth_instance
        if request is None:
            return error("Not in context.")

        if request.method == 'POST':
            req = request.json
            req_user = req.get('user_id', None)
            if req_user is None:
                print(req_user)
                return error("No user identifier")
            self.associate_user(req_user)
            self.retrieve_saved_authorization()

            if self.auth_instance is None:
                # We didn't find a pending request in the database. Drop it here because why not.
                return
            self.auth_instance.user_id = req_user

            if 'error' not in req:
                # Successful authorization
                req_key = req.get('consumer_key', None)
                req_secret = req.get('consumer_secret', None)
                key_id = req.get('key_id', None)

                target_instance.authorization_code = req_key
                target_instance.authorization_token = req_secret
                target_instance.authorization_state = key_id
                target_instance.expiration_date = datetime.datetime.max
                res = True

            self.auth_instance = target_instance
            self.update_request_instance(target_instance)
        else:
            print(request.args)

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

    def auth_login(self):
        from flask_login import current_user
        if current_user.is_authenticated:
            self.associate_user(current_user.get_id())
            self.retrieve_saved_authorization()
            destination = self.create_authorization_endpoint()
        else:
            destination = url_for('index')
        return redirect(destination)

    def auth_receive(self):
        self.receive_authorization(self.redirect_on_success, self.redirect_on_failure)
        return redirect(url_for('index'))

    def auth_purge(self):
        from flask_login import current_user
        if current_user.is_authenticated:
            self.associate_user(current_user.get_id())
            self.retrieve_saved_authorization()
            self.purge_request_instance()
        return redirect(url_for('index'))

    def auth_authorize(self):
        # If we are here then everything we need is being processed elsewhere. We can send the user back.
        return redirect(url_for('index'))
    def redirect_on_success(self):
        return redirect(url_for('index'))

    def redirect_on_failure(self, error):
        return redirect(url_for('index'))