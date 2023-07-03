from flask import url_for

from util.oauth import EtsyOAuthHandler

def login():
    redirect_uri = url_for('etsy_authorize', _external=True, _scheme='https')
    return EtsyOAuthHandler.oauth_etsy.authorize_redirect(redirect_uri)