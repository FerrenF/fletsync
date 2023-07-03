from util.oauth import EtsyOAuthHandler
from flask import session, redirect, url_for


def authorize():
    token = EtsyOAuthHandler.request_token()
    session['etsy_token'] = token
    return redirect(url_for('index'))