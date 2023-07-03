from authlib.integrations.flask_client import OAuth
from flask import Flask, url_for

from config import ETSY_API_KEY, ETSY_SHARED_SECRET

oauth = OAuth()

class EtsyOAuthHandler:

    oauth_etsy = None
    def __init__(self, app: Flask):
        if app is not None:
            self.init_oauth_handler(app)


    def init_oauth_handler(self, app: Flask):
        app.config['ETSY_CLIENT_ID'] = ETSY_API_KEY
        app.config['ETSY_CLIENT_SECRET'] = ETSY_API_KEY
        oauth.init_app(app)

        EtsyOAuthHandler.oauth_etsy = oauth.register(
            name='etsy',
            api_base_url='https://api.etsy.com/v3/',
            access_token_url='https://api.etsy.com/v3/public/oauth/token',
            authorize_url='https://www.etsy.com/oauth/connect',
            client_id=ETSY_API_KEY,
            client_secret=ETSY_SHARED_SECRET,
        )

    @staticmethod
    def request_token(additional_scope=None):
        if EtsyOAuthHandler.oauth_etsy is None:
            return None
        redirect_uri = url_for('etsy_authorize', _external=True, _scheme='https')
        return EtsyOAuthHandler.oauth_etsy.authorize_redirect(redirect_uri, scope=additional_scope)
